import datetime
import math
import os
import threading

from requests import HTTPError

from src.exceptions import ChannelNotFoundException
from src.models.channel import Channel, ChannelCache
from src.models.search_term import SearchResult
from src.models.video import Video


def get_channel_from_title(channel_cache: ChannelCache, title: str, cache_only=False):
    channel = None
    possible_titles = []

    # Build the list of titles in reverse size order
    # eg: "Halocene ft." becomes ["Halocene ft.", "Halocene"]
    title_words = title.split()
    for idx, word in enumerate(title_words):
        possible_titles.append(' '.join(title_words[:idx + 1]))
    possible_titles.reverse()

    for possible_title in possible_titles:
        if channel := channel_cache.by_title(possible_title):
            break

    if not channel and not cache_only:
        for result in SearchResult.from_term("|".join(possible_titles)):
            if channel := channel_cache.by_id(result.id) is None:
                channel = Channel.from_id(result.id)
                channel_cache.add(channel)
            for title_fragment in possible_titles:
                if channel.title == title_fragment:
                    return channel


def get_target_channel(channel_name: str) -> Channel:
    try:
        searches = SearchResult.from_term(channel_name)
        match = [s for s in searches if s.title == channel_name]
        if not match:
            raise ChannelNotFoundException(channel_name)
    except HTTPError:
        raise ChannelNotFoundException(channel_name)
    return Channel.from_id(match[0].id)


def build_channel_cache(uploads, channel_cache):
    channel_ids = set()
    channel_titles = set()
    channel_urls = set()
    channel_usernames = set()
    video_ids = set()

    for video in uploads:
        channel_ids.update(video.get_channel_ids_from_description())
        channel_titles.update(video.get_channel_titles_from_title())
        channel_urls.update(video.get_urls_from_description())
        channel_usernames.update(video.get_users_from_description())
        video_ids.update(video.get_video_ids_from_description())

    for _ in channel_ids:
        try:
            channel_cache.add(Channel.from_id(_))
        except HTTPError:
            print(f"Failed retrieving channel for id: {_}")

    for _ in channel_titles:
        if not channel_cache.by_title(_):
            try:
                channel_cache.add(get_channel_from_title(channel_cache, _))
            except HTTPError:
                print(f"Failed retrieving channel for title: {_}")

    for _ in channel_urls:
        if not channel_cache.by_url(_):
            try:
                channel_cache.add(Channel.from_url(_))
            except HTTPError:
                print(f"Failed retrieving channel for URL: {_}")

    for _ in channel_usernames:
        if not channel_cache.by_username(_):
            try:
                new_channel = Channel.from_username(_)
                # Username can be queried, but isn't returned by the API
                # This if statement saves the username in the cache, allowing later reuse
                if old_channel := channel_cache.by_id(new_channel.id):
                    old_channel.username = _
                else:
                    channel_cache.add(new_channel)
            except HTTPError:
                print(f"Failed retrieving channel for username: {_}")

    for _ in video_ids:
        try:
            video = Video.from_id(_)
            if not channel_cache.by_id(video.channel_id):
                channel_cache.add(Channel.from_id(video.channel_id))
        except HTTPError:
            print(f"Failed retrieving video for ID: {_}")


def get_collaborations(uploads: list, channel_cache: ChannelCache, out_collaborations: dict):

    def update_collaborations():
        if channel == host_channel:
            return
        if out_collaborations[host_channel].get(channel) is None:
            out_collaborations[host_channel][channel] = []
        out_collaborations[host_channel][channel].append(video)

    for video in uploads:
        host_channel = channel_cache.by_id(video.channel_id)
        if out_collaborations.get(host_channel) is None:
            out_collaborations[host_channel] = {}

        for channel_id in video.get_channel_ids_from_description():
            if channel := channel_cache.by_id(channel_id):
                update_collaborations()

        for possible_title in video.get_channel_titles_from_title():
            if channel := get_channel_from_title(channel_cache, possible_title, cache_only=True):
                update_collaborations()

        for url in video.get_urls_from_description():
            if channel := channel_cache.by_url(url):
                update_collaborations()

        for username in video.get_users_from_description():
            if channel := channel_cache.by_username(username):
                update_collaborations()

        for video_id in video.get_video_ids_from_description():
            try:
                linked_video = Video.from_id(video_id)
                if channel := channel_cache.by_id(linked_video.channel_id):
                    update_collaborations()
            except HTTPError:
                print(f"Failed to find linked video {video_id} from video {video}")


def get_uploads(channel: Channel, uploads: list):
    uploads.extend(Video.from_channel(channel))


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def lambda_handler(event, context):
    print(datetime.datetime.now())
    channel_cache = ChannelCache()
    target_channel = get_target_channel(event['target_channel'])
    channel_cache.add(target_channel)
    build_channel_cache(Video.from_channel(target_channel), channel_cache)

    all_uploads = []
    upload_threads = []
    for channel in channel_cache.cache:
        t = threading.Thread(target=get_uploads,
                             args=(channel, all_uploads))
        t.start()
        upload_threads.append(t)
    for thread in upload_threads:
        thread.join()

    collab_threads = []
    collabs = {}
    num_threads = os.getenv("NUM_THREADS", 200)

    for chunk in chunks(all_uploads, math.ceil(len(all_uploads) / num_threads)):
        t = threading.Thread(target=get_collaborations,
                             args=(chunk, channel_cache, collabs))
        t.start()
        collab_threads.append(t)

    for thread in collab_threads:
        thread.join()

    print(datetime.datetime.now())
    print(collabs)
