import random

import requests
from bs4 import BeautifulSoup
from requests import HTTPError

from src.caches.channel_cache import ChannelCache, PartnersCache
from src.caches.search_cache import SearchCache
from src.caches.video_cache import VideoCache
from src.enums import ChannelFilters
from src.models.video import Video


def get_target_channel(target_name: str):
    searches = SearchCache.add(target_name)
    target_channel = [s for s in searches if s.title == target_name][0]
    if not target_channel:
        raise RuntimeError(f"Couldn't find target channel: '{target_name}'")
    PartnersCache.add(ChannelFilters.ID, target_channel.result_id)


def get_channel_ids_from_description(video: Video) -> list:
    channel_ids = []
    channel_ids.extend(video.get_collaborator_ids_from_description())

    for user in video.get_collaborator_users_from_description():
        try:
            channel_ids.append(ChannelCache.add(ChannelFilters.USERNAME, user).id)
        except HTTPError as e:
            print(f"ERROR whilst processing user '{user}' - {e}")
            continue

    for video_id in video.get_video_ids_from_description():
        try:
            channel_ids.append(VideoCache.add(video_id).channel_id)
        except HTTPError as e:
            print(f"ERROR whilst processing video_id '{video_id}' - {e}")
            continue

    for url in video.get_collaborator_urls_from_description():
        channel = ChannelCache.get_from_cache(ChannelFilters.URL, url) or ChannelCache.get_from_cache(ChannelFilters.USERNAME, url)
        if channel:
            channel_ids.append(channel.id)
            continue
        print(f"Making soup from '{url}'")
        response = requests.get(f'https://www.youtube.com/{url}',
                                cookies={'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(random.randint(100, 999))})
        if response.status_code == 200:
            soup = BeautifulSoup(response.content.decode(), 'html.parser')
            if og_url := soup.find('meta', property='og:url'):
                channel_id = og_url['content'].split("/")[-1]
                channel_ids.append(channel_id)
                # Some URLs of the form 'youtube.com/url' are actually usernames,
                # redirecting to 'youtube.com/user/url' or 'youtube.com/c/<actual_url>'.
                # This logic ensures that we've stored this properly for future use of the cache
                if "/user/" in response.url or response.url.split("/")[-1].lower() != url.lower():
                    ChannelCache.add(ChannelFilters.USERNAME, url)
                else:
                    ChannelCache.add(ChannelFilters.ID, channel_id)
                continue

        print(f"ERROR - Spilled soup with code {response.status_code} - {response.content}")
    return channel_ids


def find_channel_by_title(search_results, possible_titles):
    # Abstracted to separate method to allow return from nested loop
    for result in search_results:
        guest = ChannelCache.add(ChannelFilters.ID, result.result_id)
        for title_fragment in possible_titles:
            if guest.title == title_fragment:
                return guest


def get_channel_ids_from_title(video: Video) -> list:
    """
    There's no delimiter to show how many words after the @ in a video title are the actual channel title
    eg: Crocodile Rock (@Halocene ft. @Violet Orlandi @Lollia. "Violet Orlandi" is a channel name,
    but "Halocene ft." is not, the actual channel name is "Halocene"
    To accommodate this, we search for all possible combination of words that could make up
    the channel name. eg: "Halocene|Halocene ft." / "Violet|Violet Orlandi" / "Lollia"
    We assume the longest successful match is the correct one.
    """
    channel_ids = []

    for title in video.get_collaborators_from_title():
        possible_titles = []
        title_words = title.split()
        for idx, word in enumerate(title_words):
            possible_titles.append(' '.join(title_words[:idx + 1]))
        try:
            search_results = SearchCache.add("|".join(possible_titles))
            possible_titles.reverse()
            guest = find_channel_by_title(search_results, possible_titles)
        except HTTPError:
            print(f"ERROR - Could not find channel with title '{title}'")
        else:
            if guest:
                channel_ids.append(guest.id)

    return channel_ids
