from src.models.channel import Channel
from src.models.search import SearchResult


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
    pass

    # Get Channel object for given channel name

    # Get list of channels referenced by videos of th given channel

    # Get list of videos uploaded by given and all referenced channels

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
