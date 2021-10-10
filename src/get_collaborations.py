import datetime

from requests import HTTPError

from src.exceptions import ChannelNotFoundException
from src.models.channel import Channel, ChannelCache
from src.models.search_term import SearchResult
from src.models.video import Video


def get_channel_from_title(channel_cache: ChannelCache, title: str):

    def find_channel_by_title(results, titles):
        # Separate method to allow return from nested loop
        for result in results:
            guest = channel_cache.by_id(result.id) or Channel.from_id(result.id)
            for title_fragment in titles:
                if guest.title == title_fragment:
                    return guest

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

    if not channel:
        if search_results := SearchResult.from_term("|".join(possible_titles)):
            channel = find_channel_by_title(search_results, possible_titles)

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


def lambda_handler(event, context):
    print(datetime.datetime.now())
    channel_cache = ChannelCache()
    target_channel = get_target_channel(event['target_channel'])
    uploads = Video.from_channel(target_channel)

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
        channel_cache.add(Channel.from_id(_))

    for _ in channel_titles:
        if not channel_cache.by_title(_):
            channel_cache.add(get_channel_from_title(channel_cache, _))

    for _ in channel_urls:
        if not channel_cache.by_url(_):
            channel_cache.add(Channel.from_url(_))

    for _ in channel_usernames:
        channel_cache.add(Channel.from_username(_))

    for _ in video_ids:
        video = Video.from_id(_)
        if not channel_cache.by_id(video.channel_id):
            channel_cache.add(Channel.from_id(video.channel_id))

    print(datetime.datetime.now())
    channel_cache.print()
