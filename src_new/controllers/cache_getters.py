from sqlalchemy import or_

from src_new.models.channel import Channel
from src_new.models.video import Video


def get_channels_from_description(video: Video) -> set:
    channels = set()

    for channel_id in video.get_collaborator_ids_from_description():
        if cache_by_id := Channel.from_cache("id", channel_id):
            channels.update([cache_by_id])

    for user in video.get_collaborator_users_from_description():
        if cache_by_user := Channel.from_cache("forUsername", user):
            channels.update([cache_by_user])

    for video_id in video.get_video_ids_from_description():
        if featured_video := Video.from_cache(video_id):
            if cache_by_video := Channel.from_cache("id", featured_video.channel_id):
                channels.update([cache_by_video])

    for url in video.get_collaborator_urls_from_description():
        if cache_by_url := Channel.query.filter(or_(Channel.url == url.lower(), Channel.forUsername == url.lower())).first():
            channels.update([cache_by_url])

    return channels


def get_channels_from_title(video: Video) -> set:
    """
    There's no delimiter to show how many words after the @ in a video title are the actual channel title
    eg: Crocodile Rock (@Halocene ft. @Violet Orlandi @Lollia. "Violet Orlandi" is a channel name,
    but "Halocene ft." is not, the actual channel name is "Halocene"
    To accommodate this, we search for all possible combination of words that could make up
    the channel name. eg: "Halocene|Halocene ft." / "Violet|Violet Orlandi" / "Lollia"
    We assume the longest successful match is the correct one.
    """
    channels = set

    for title in video.get_collaborators_from_title():
        possible_titles = []

        title_words = title.split()
        for idx, word in enumerate(title_words):
            possible_titles.append(' '.join(title_words[:idx + 1]))
        possible_titles.reverse()

        for possible_title in possible_titles:
            if guest := Channel.query.filter_by(title=possible_title).first():
                channels.update([guest])
                break

    return channels
