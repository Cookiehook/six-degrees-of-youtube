import logging
from multiprocessing import Pool

import requests
from flask import url_for
from flask_sqlalchemy_session import current_session
from requests import HTTPError

from src.controllers.exceptions import ChannelNotFoundException, YoutubeAuthenticationException
from src.models.channel import Channel
from src.models.collaboration import Collaboration
from src.models.history import History
from src.models.search import SearchResult
from src.models.video import Video

logger = logging.getLogger()


def get_chunks(data, n):
    return [data[i::n] for i in range(n)]


def get_collaborations_for_channel(channel_name: str, previous_channel_name: str) -> list:
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
    try:
        # Get list of collaborators present in target channel's uploads (including target channel)
        host_videos = [v.id for v in Video.from_channel(target_channel)]

        if host_videos:
            parallelism = 80
            pool = Pool(parallelism)  # Only instantiate pool if there's work to do, as it's expensive

            logger.info(f"Retrieving guest channels for {target_channel}")
            guest_channels = {target_channel.id}
            host_videos_chunks = get_chunks(host_videos, parallelism)
            starmap_args = [[url_for('graph.get_collaborators_for_videos', _external=True), list] for list in host_videos_chunks]
            for result in pool.starmap(request_guest_channels_for_video, starmap_args):
                guest_channels.update(result)

            # Get all videos uploaded by all collaborators (including target channel)
            logger.info(f"Retrieving all videos for {target_channel}")
            all_videos = []
            starmap_args = [[url_for('graph.get_uploads_for_channel', _external=True), c] for c in guest_channels]
            for result in pool.starmap(request_videos_for_channel, starmap_args):
                all_videos.extend(result)

            # Calculate all collaborations between collaborators (including target channel)
            if all_videos:
                logger.info(f"Calculating collaborations for {target_channel}")
                all_videos_chunks = get_chunks(all_videos, parallelism)
                starmap_args = [[url_for('graph.process_collaborations', _external=True), target_channel.id, videos] for videos in all_videos_chunks]
                pool.starmap(request_process_collaborations, starmap_args)
            logger.info(f"Finished processing channel {target_channel}")
            target_channel.processed = True
            current_session.commit()
        History.add(target_channel)
    except YoutubeAuthenticationException as e:
        if len(Video.from_channel(target_channel, cache_only=True)) > 0:
            logger.warning(f"Encountered authentication error whilst processing channel '{channel_name}' - {e}")
            logger.warning("Some videos already present, returning collaborations from cache")
        else:
            raise

    if previous_channel_name:
        previous_channel = Channel.from_title(previous_channel_name)
        return Collaboration.for_target_channel(target_channel) + Collaboration.for_target_channel(previous_channel)
    else:
        return Collaboration.for_target_channel(target_channel)


def request_videos_for_channel(url, channel_id):
    resp = requests.post(url, json={'channel': channel_id})
    return resp.json()['videos']


def request_guest_channels_for_video(url, videos):
    resp = requests.post(url, json={'videos': videos})
    return resp.json()['channels']


def request_process_collaborations(url, target_channel, videos):
    requests.post(url, json={'videos': videos, 'target_channel': target_channel})


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


def get_uploads_for_channel(channel_id: str) -> list:
    videos = []
    channel = Channel.from_id(channel_id)
    logger.info(f"Getting uploads for channel '{channel}'")
    try:
        videos.extend([v.id for v in Video.from_channel(channel)])
    except HTTPError as e:
        logger.error(f"Processing uploads for channel '{channel}' - '{e}'")
    return videos


def populate_collaborations(target_channel_id: str, videos: list):
    """
    Iterate through a list of video objects, and create a Collaboration object
    for each identified work. These aren't returned as a later stage extracts all
    relevant collaborations from the database, populated by multiple threads

    :param videos: list of videos to process
    :param target_channel_id: Channel id that relationships are being calculated for.
    """
    target_channel = Channel.from_id(target_channel_id)
    for video_id in videos:
        video = Video.from_id(video_id)
        logger.debug(f"Populating collaborations for video '{video}'")
        collaborators = set()
        host = Channel.from_id(video.channel_id, cache_only=True)
        collaborators.update(get_channels_from_description(video, cache_only=True))
        collaborators.update(get_channels_from_title(video, cache_only=True))
        for guest in collaborators:
            existing_collabs = Collaboration.for_video(video)
            if host.id == guest.id:
                continue  # Happens when an artist references another of their videos in the description
            if any({collab.channel_1_id, collab.channel_2_id} == {host.id, guest.id} for collab in existing_collabs):
                continue  # Happens when we're re-processing this video in the context of another channel
            current_session.add(Collaboration(host, guest, video))
        video.processed_for += "|" + target_channel.id
        current_session.commit()
