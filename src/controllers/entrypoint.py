import multiprocessing

from flask import current_app
from requests import HTTPError

from src.controllers import api_getters, cache_getters
from src.models.channel import Channel
from src.models.collaboration import Collaboration
from src.models.video import Video


def chunkify(list, chunks):
    return [list[i::10] for i in range(chunks)]


def entrypoint(channel_name):
    target_channel = api_getters.get_target_channel(channel_name)
    target_channel_id = target_channel.id
    guest_channels = set()
    for video in Video.from_uploads(target_channel):
        guest_channels.update(api_getters.get_channel_ids_from_description(video))
        guest_channels.update(api_getters.get_channel_ids_from_title(video))

    # Get all videos we need to process, regardless of channel ownership
    # TODO - Make this multithreaded too. Maybe scale the whole thing with external lambdas rather than threads?
    videos = []
    for channel_id in guest_channels:
        try:
            channel = Channel.from_cache('id', channel_id)
            videos.extend([v.id for v in Video.from_uploads(channel)])
        except HTTPError as e:
            print(f"ERROR whilst getting uploads for {channel} - {e}")
    # Divide list of videos into 10 similarly sized chunks, then process in parallel
    processes = []
    for chunk in chunkify(videos, 10):
        processes.append(multiprocessing.Process(target=populate_collaborations, args=(chunk,)))

    for process in processes:
        with current_app.app_context():
            process.start()
    for process in processes:
        process.join()

    collabs = Collaboration.get_for_channel(target_channel_id)
    for c in collabs:
        print(c)


def populate_collaborations(video_ids):
    for video_id in video_ids:
        video = Video.from_cache(video_id)
        collaborators = set()
        host = Channel.from_cache("id", video.channel_id)
        collaborators.update(cache_getters.get_channels_from_description(video))
        collaborators.update(cache_getters.get_channels_from_title(video))
        for guest in collaborators:
            if host.id == guest.id:
                continue  # Happens when an artist references another of their videos in the description
            Collaboration(host, guest, video)
