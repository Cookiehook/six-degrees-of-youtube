from requests import HTTPError

from src_new.controllers import api_getters, cache_getters
from src_new.models.channel import Channel
from src_new.models.collaboration import CollaborationCache
from src_new.models.video import Video


def entrypoint(channel_name):
    target_channel = api_getters.get_target_channel(channel_name)
    guest_channels = set()
    for video in Video.from_uploads(target_channel):
        guest_channels.update(api_getters.get_channel_ids_from_description(video))
        guest_channels.update(api_getters.get_channel_ids_from_title(video))

    video_set = set()
    for channel_id in sorted(list(guest_channels)):
        channel = Channel.from_cache("id", channel_id)
        try:
            video_set.update(Video.from_uploads(channel))
        except HTTPError as e:
            print(f"ERROR - Could not find uploads playlist for {channel} - {e}")

    for video in video_set:
        collaborators = set()
        host = Channel.from_cache("id", video.channel_id)
        collaborators.update(cache_getters.get_channels_from_description(video))
        collaborators.update(cache_getters.get_channels_from_title(video))
        for guest in collaborators:
            CollaborationCache.add(host, guest, video)

    for c in CollaborationCache.collection:
        print(c)
