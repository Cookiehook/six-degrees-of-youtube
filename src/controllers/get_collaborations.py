import logging
import os
from multiprocessing import Process

from requests import HTTPError

from src.controllers.exceptions import ChannelNotFoundException, YoutubeAuthenticationException
from src.models.channel import Channel
from src.models.collaboration import Collaboration
from src.models.history import History
from src.models.search import SearchResult
from src.models.video import Video

logger = logging.getLogger()


def get_collaborations_for_channel(channel_name: str) -> list:
    """
    Identifies all collaborations that a particular channel has made by parsing tags and hyperlinks
    in all videos uploaded by that channel. A collaboration instance is created for each.

    A collaboration object records the video that was created, the uploading channel and referenced channel.
    If multiple channels collaborated on one video, a collaboration object is created for the host and each referenced channel.
    Therefore one video may be referenced in several collaborations

    :param channel_name: Name of channel to parse, as shown on the Youtube webpage.
    :return: list of Collaboration objects.
    """
    target_channel = get_target_channel(channel_name)
    logger.info(f"Found target channel '{target_channel}'")
    guest_channels = {target_channel}
    # TODO - Make this multi-threaded too. Maybe scale the whole thing with external lambdas rather than threads?
    try:
        for video in Video.from_channel(target_channel):
            logger.debug(f"Parsing host video '{video}'")
            guest_channels.update(get_channels_from_description(video))
            guest_channels.update(get_channels_from_title(video))

        videos = get_uploads_for_channels(guest_channels)

        if videos:
            processes = distribute_videos(target_channel.id, videos)
            process_threads(processes)
        target_channel.processed = True
        History.add(target_channel)
        Video.commit()
    except YoutubeAuthenticationException as e:
        if len(Video.from_channel(target_channel, cache_only=True)) > 0:
            logger.warning(f"Encountered authentication error whilst processing channel '{channel_name}' - {e}")
            logger.warning("Some videos already present, returning collaborations from cache")
        else:
            raise

    return Collaboration.for_target_channel(target_channel)


def get_target_channel(channel_name: str) -> Channel:
    """
    Get Channel object matching the given name.

    :param channel_name: Name of channel, as seen on Youtube webpage
    :return: Channel instance for that channel
    :raises: ChannelNotFoundException if the channel can't be found.
    """
    try:
        searches = SearchResult.from_term(channel_name)
        match = [s for s in searches if s.title == channel_name]
        if not match:
            raise ChannelNotFoundException(channel_name)
    except HTTPError:
        raise ChannelNotFoundException(channel_name)
    return Channel.from_id(match[0].id)


def get_channels_from_description(video: Video, cache_only=False) -> set:
    """
    Retrieve set of Channel objects for all channels referenced in
    the given video description.

    :param video: Video to parse
    :param cache_only: Default False. If True, only search the cache.
    :return: set of Channel objects for referenced channels
    """
    channels = set()

    for channel_id in video.get_channel_ids_from_description():
        try:
            if channel_by_id := Channel.from_id(channel_id, cache_only=cache_only):
                channels.update([channel_by_id])
        except HTTPError as err:
            logger.error(f"Failed processing channel ID '{channel_id}' from video '{video}' - {err}")

    for username in video.get_users_from_description():
        try:
            if channel_by_name := Channel.from_username(username, cache_only=cache_only):
                channels.update([channel_by_name])
        except HTTPError as err:
            logger.error(f"Failed processing username '{username}' from video '{video}' - {err}")

    for video_id in video.get_video_ids_from_description():
        try:
            if linked_video := Video.from_id(video_id, cache_only=cache_only):
                if channel_by_vid := Channel.from_id(linked_video.channel_id, cache_only=cache_only):
                    channels.update([channel_by_vid])
        except HTTPError as err:
            logger.error(f"Failed processing video ID '{video_id}' from video '{video}' - {err}")

    for url in video.get_urls_from_description():
        try:
            if channel_by_url := Channel.from_url(url, cache_only=cache_only):
                channels.update([channel_by_url])
        except HTTPError as err:
            logger.error(f"Failed processing url '{url}' from video '{video}' - {err}")

    return channels


def get_channels_from_title(video: Video, cache_only=False) -> set:
    """
    Retrieve set of Channel objects for all channels referenced in the given video title.
    There's no delimiter to show how many words after the @ in a video title are the actual channel title
    eg: Crocodile Rock (@Halocene ft. @Violet Orlandi @Lollia).
    "Violet Orlandi" is a channel name, but "Halocene ft." is not, the actual channel name is "Halocene"
    To accommodate this, we search for all possible combination of words that could make up
    the channel name. eg: "Halocene|Halocene ft." / "Violet|Violet Orlandi" / "Lollia"
    We assume the longest successful match is the correct one.

    :param video: Video to parse
    :param cache_only: Default False. If True, only search the cache.
    :return: set of Channel objects for referenced channels
    """

    def find_channel_by_title(results, titles):
        # Separate method to allow return from nested loop
        for result in results:
            guest = Channel.from_id(result.id)
            for title_fragment in titles:
                if guest.title == title_fragment:
                    return guest

    channels = set()

    for title in video.get_collaborators_from_title():
        guest = None
        possible_titles = []

        # Build the list of titles in reverse size order
        # eg: "Halocene ft." becomes ["Halocene ft.", "Halocene"]
        title_words = title.split()
        for idx, word in enumerate(title_words):
            possible_titles.append(' '.join(title_words[:idx + 1]))
        possible_titles.reverse()

        for possible_title in possible_titles:
            if guest := Channel.from_title(possible_title):
                break

        if not guest:
            try:
                if search_results := SearchResult.from_term("|".join(possible_titles), cache_only=cache_only):
                    guest = find_channel_by_title(search_results, possible_titles)
            except HTTPError as err:
                logger.error(f"Processing search term '{possible_titles}' for video '{video}' - '{err}'")

        if guest:
            channels.update([guest])
        elif not cache_only:
            logger.error(f"Processing channel name '{title}' from title of '{video}' failed")

    return channels


def get_uploads_for_channels(channels: set) -> list:
    """
    Retrieve list of all videos uploaded by a list of channels

    :param channels: set of Channel objects
    :return: list of Video objects for all channels
    """
    videos = []
    for channel in channels:
        logger.info(f"Getting uploads for channel '{channel}'")
        try:
            videos.extend([v.id for v in Video.from_channel(channel)])
        except HTTPError as e:
            logger.error(f"Processing uploads for channel '{channel}' - '{e}'")

    return videos


def distribute_videos(target_channel_id: str, videos: list) -> list:
    """
    Split the list of videos into 10 similarly sized groups
    and create a thread to process each list

    :param videos: list of Video objects
    :param target_channel_id: Channel ID that relationships are being calculated for
    :return: list of Process objects
    """

    processes = []
    for chunk in [videos[i::10] for i in range(10)]:
        processes.append(Process(target=populate_collaborations, args=(target_channel_id, chunk)))
    return processes


def process_threads(processes: list):
    """
    Start all processes and wait for completion

    :param processes: list of process objects
    :return:
    """
    for process in processes:
        process.start()
    for process in processes:
        process.join()


def populate_collaborations(target_channel_id: str, videos: list):
    """
    Iterate through a list of video objects, and create a Collaboration object
    for each identified work. These aren't returned as a later stage extracts all
    relevant collaborations from the database, populated by multiple threads

    :param videos: list of videos to process
    :param target_channel_id: Channel id that relationships are being calculated for.
    """
    target_channel = Channel.from_id(target_channel_id)
    logger.info(f"Populating collaborations for PID '{os.getpid()}'")
    for video_id in videos:
        video = Video.from_id(video_id)
        logger.debug(f"Populating collaborations for video '{video}'")
        collaborators = set()
        host = Channel.from_id(video.channel_id, cache_only=True)
        collaborators.update(get_channels_from_description(video, cache_only=True))
        collaborators.update(get_channels_from_title(video, cache_only=True))
        for guest in collaborators:
            existing_collabs = Collaboration.for_video(video)
            collab = Collaboration(host, guest, video)
            if host.id == guest.id:
                continue  # Happens when an artist references another of their videos in the description
            if collab in existing_collabs:
                continue  # Happens when we're re-processing this video in the context of another channel
            collab.commit()
        video.processed_for += "|" + target_channel.id
    Video.commit()
