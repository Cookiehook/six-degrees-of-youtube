import logging

from requests import HTTPError

from src.models.channel import Channel
from src.models.search import SearchResult
from src.models.video import Video

logger = logging.getLogger()


def get_collaborations_for_channel(channel_name: str) -> list:
    """
    Identifies all collaborations that a particular channel has made by:
        1) Retrieves all videos uploaded by the given channel.
        2) Search for any channels referenced in those videos, by tags or hyperlinks.
        3) Retrieve all referenced channels and their uploads.
        4) Parse all videos from step 1 and 3, creating collaboration objects for each video and channel pairing.
        5) Return any collaboration objects where both channels are the input channel or in the list from step 3.

    A collaboration object records the video that was created, the uploading channel and referenced channel.
    If multiple channels collaborated on one video, a collaboration object is created for the host and each referenced channel.
    Therefore one video may be referenced in several collaborations

    :param channel_name: Name of channel to parse, as shown on the Youtube webpage.
    :return: list of Collaboration objects.
    """
    target_channel = get_target_channel(channel_name)
    guest_channels = set()
    for video in Video.from_channel(target_channel):
        guest_channels.update(get_channels_from_description(video))
        guest_channels.update(get_channels_from_title(video))

    # Get list of videos uploaded by the given channel and all referenced channels

    # Split list of videos into similarly sized groups for parallel processing

    # Create Collaboration objects for each video

    # Return Collaborations relevant for the given artist


def get_target_channel(channel_name: str) -> Channel:
    """
    Get Channel object matching the given name.

    :param channel_name: Name of channel, as seen on Youtube webpage
    :return: Channel instance for that channel
    :raises: RuntimeError if the channel can't be found.
    """
    searches = SearchResult.from_term(channel_name)
    match = [s for s in searches if s.title == channel_name]
    if not match:
        raise RuntimeError(f"Could not find target channel: {channel_name}")
    return Channel.from_id(match[0].id)


def get_channels_from_description(video: Video) -> set:
    """
    Retrieve set of Channel objects for all channels referenced in
    the given video description.

    :param video: Video to parse
    :return: set of Channel objects for referenced channels
    """
    channels = set()

    for channel_id in video.get_channel_ids_from_description():
        try:
            channels.update([Channel.from_id(channel_id)])
        except HTTPError as err:
            logger.error(f"Failed processing channel ID '{channel_id}' from video '{video}' - {err}")

    for username in video.get_users_from_description():
        try:
            channels.update([Channel.from_username(username)])
        except HTTPError as err:
            logger.error(f"Failed processing username '{username}' from video '{video}' - {err}")

    for video_id in video.get_video_ids_from_description():
        try:
            linked_video = Video.from_id(video_id)
            channels.update([Channel.from_id(linked_video.channel_id)])
        except HTTPError as err:
            logger.error(f"Failed processing video ID '{video_id}' from video '{video}' - {err}")

    for url in video.get_urls_from_description():
        try:
            channels.update([Channel.from_url(url)])
        except HTTPError as err:
            logger.error(f"Failed processing url '{url}' from video '{video}' - {err}")

    return channels


def get_channels_from_title(video: Video) -> set:
    """
    Retrieve set of Channel objects for all channels referenced in the given video title.
    There's no delimiter to show how many words after the @ in a video title are the actual channel title
    eg: Crocodile Rock (@Halocene ft. @Violet Orlandi @Lollia).
    "Violet Orlandi" is a channel name, but "Halocene ft." is not, the actual channel name is "Halocene"
    To accommodate this, we search for all possible combination of words that could make up
    the channel name. eg: "Halocene|Halocene ft." / "Violet|Violet Orlandi" / "Lollia"
    We assume the longest successful match is the correct one.

    :param video: Video to parse
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
                search_results = SearchResult.from_term("|".join(possible_titles))
                guest = find_channel_by_title(search_results, possible_titles)
            except HTTPError as err:
                logger.error(f"Processing search term '{possible_titles}' for video '{video}' - '{err}")

        if guest:
            channels.update([guest])
        else:
            logger.error(f"Processing channel name '{title}' from title of '{video}' failed")

    return channels
