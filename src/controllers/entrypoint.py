import multiprocessing

from flask import current_app
from requests import HTTPError

from src.controllers import api_getters, cache_getters
from src.models.channel import Channel
from src.models.collaboration import Collaboration
from src.models.video import Video


def entrypoint(channel_name):
    target_channel = api_getters.get_target_channel(channel_name)
    target_channel_id = target_channel.id
    guest_channels = set()
    for video in Video.from_uploads(target_channel):
        guest_channels.update(api_getters.get_channel_ids_from_description(video))
        guest_channels.update(api_getters.get_channel_ids_from_title(video))

    processes = []
    for channel_id in sorted(list(guest_channels)):
        processes.append(multiprocessing.Process(target=populate_collaborations, args=(channel_id,)))

    for process in processes:
        with current_app.app_context():
            process.start()

    for process in processes:
        process.join()

    collabs = Collaboration.get_for_channel(target_channel_id)
    for c in collabs:
        print(c)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def populate_collaborations(channel_id):
    channel = Channel.from_cache("id", channel_id)
    try:
        videos = Video.from_uploads(channel)
    except HTTPError as e:
        print(f"ERROR - Could not find uploads playlist for {channel} - {e}")
        return

    for video in videos:
        collaborators = set()
        host = Channel.from_cache("id", video.channel_id)
        collaborators.update(cache_getters.get_channels_from_description(video))
        collaborators.update(cache_getters.get_channels_from_title(video))
        for guest in collaborators:
            if host.id == guest.id:
                continue  # Happens when an artist references another of their videos in the description
            Collaboration(host, guest, video)
