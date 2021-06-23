from copy import copy

from requests import HTTPError

from src.caches.channel_cache import PartnersCache
from src.caches.collaboration_cache import CollaborationCache
from src.caches.video_cache import VideoCache
from src.controllers import get_cached, get_from_api
from src.enums import ChannelFilters
from src.models.video import Video


def entrypoint(channel_name):
    get_from_api.get_target_channel(channel_name)
    final_iteration = 2
    iteration = 1
    while iteration < final_iteration:
        channel_loop = copy(PartnersCache.collection)
        for host in channel_loop:
            print(f"Processing channel - {host.title}")
            for video in Video.from_playlist(host.uploads_id):
                VideoCache.collection[video.video_id] = video
                guest_channels = get_from_api.get_channels_from_description(video)
                guest_channels.extend(get_from_api.get_channels_from_title(video))
                for channel_id in guest_channels:
                    try:
                        PartnersCache.add(ChannelFilters.ID, channel_id)
                    except HTTPError as e:
                        print(f"ERROR whilst processing channel_id '{channel_id}' - {e}")
                        continue
        iteration += 1

    for channel in PartnersCache.collection[1:]:
        try:
            videos = Video.from_playlist(channel.uploads_id)
            VideoCache.collection.update({i.video_id: i for i in videos})
        except HTTPError as e:
            if e.args[0].get('error', {}).get('code') == 404:
                print(f"ERROR - Could not find uploads playlist for {channel}")
            else:
                raise

    print("Processing cached videos")
    for video_id, video in VideoCache.collection.items():
        host = PartnersCache.get_from_cache(ChannelFilters.ID, video.channel_id)
        guest_channels = get_cached.get_cached_channels_from_description(video)
        guest_channels.extend(get_cached.get_cached_channels_from_title(video))
        for guest in guest_channels:
            CollaborationCache.add(host, guest, video)

    for collab in CollaborationCache.collection:
        print(collab)

    return CollaborationCache.collection
