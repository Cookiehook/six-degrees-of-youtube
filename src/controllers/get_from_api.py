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
        channel = ChannelCache.get_from_cache(ChannelFilters.URL, url)
        if channel:
            channel_ids.append(channel.id)
            continue

        for result in SearchCache.add(url, 'channel,video'):
            if result.kind == 'youtube#channel':
                potential_id = result.result_id
            else:
                video = VideoCache.add(result.result_id)
                potential_id = video.channel_id

            potential_channel = ChannelCache.add(ChannelFilters.ID, potential_id)
            if potential_channel.url.upper() == url.upper():
                channel_ids.append(potential_id)
                break

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
