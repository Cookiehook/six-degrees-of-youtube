from src_new.controllers import api_getters
from src_new.models.channel import Channel
from src_new.models.video import Video


def entrypoint(channel_name):
    target_channel = api_getters.get_target_channel(channel_name)
    guest_channels = set()
    for video in Video.from_uploads(target_channel):
        guest_channels.update(api_getters.get_channel_ids_from_description(video))
        guest_channels.update(api_getters.get_channel_ids_from_title(video))

    video_set = set()
    for channel_id in guest_channels:
        channel = Channel.from_cache("id", channel_id)
        video_set.update(Video.from_uploads(channel))
    print()
