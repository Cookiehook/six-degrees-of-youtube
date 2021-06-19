from requests import HTTPError

from src.caches.channel_cache import ChannelCache
from src.caches.video_cache import VideoCache
from src.enums import ChannelFilters
from src.models.video import Video


def get_cached_channels_from_description(video: Video):
    channels = []

    for channel_id in video.get_collaborator_ids_from_description():
        if channel := ChannelCache.get_from_cache(ChannelFilters.ID, channel_id):
            channels.append(channel)

    for user in video.get_collaborator_users_from_description():
        if channel := ChannelCache.get_from_cache(ChannelFilters.USERNAME, user):
            channels.append(channel)

    for video_id in video.get_video_ids_from_description():
        try:
            if related_video := VideoCache.get_from_cache(video_id):
                if channel := ChannelCache.get_from_cache(ChannelFilters.ID, related_video.channel_id):
                    channels.append(channel)
        except HTTPError:
            print(f"ERROR - Could not get video from cache '{video_id}'")

    for url in video.get_collaborator_urls_from_description():
        if channel := ChannelCache.get_from_cache(ChannelFilters.URL, url):
            channels.append(channel)

    return channels


def get_cached_channels_from_title(video: Video):
    channels = []

    for title in video.get_collaborators_from_title():
        possible_titles = []
        title_words = title.split()
        for idx, word in enumerate(title_words):
            possible_titles.append(' '.join(title_words[:idx + 1]))
        possible_titles.reverse()
        guest = find_cached_channel_by_title(possible_titles)
        if guest:
            channels.append(guest)

    return channels


def find_cached_channel_by_title(possible_titles):
    for channel in ChannelCache.collection:
        for title_fragment in possible_titles:
            if channel.title == title_fragment:
                return channel
