from requests import HTTPError
from sqlalchemy import or_

from src_new.models import search
from src_new.models.channel import Channel
from src_new.models.video import Video


def get_target_channel(target_name: str):
    searches = search.from_api(target_name)
    matching_result = [s for s in searches if s.title == target_name][0]
    if not matching_result:
        raise RuntimeError(f"Couldn't find target channel: '{target_name}'")

    return Channel.from_api('id', matching_result.result_id)


def get_channel_ids_from_description(video: Video) -> set:
    channel_ids = set()

    for channel_id in video.get_collaborator_ids_from_description():
        try:
            channel_ids.update([Channel.from_api("id", channel_id).id])
        except HTTPError as e:
            print(f"ERROR whilst processing channel '{channel_id}' - {e}")
            continue

    for user in video.get_collaborator_users_from_description():
        try:
            channel_ids.update([Channel.from_api("forUsername", user).id])
        except HTTPError as e:
            print(f"ERROR whilst processing user '{user}' - {e}")
            continue

    for video_id in video.get_video_ids_from_description():
        try:
            featured_video = Video.from_api(video_id)
            channel_ids.update([Channel.from_api("id", featured_video.channel_id).id])
        except HTTPError as e:
            print(f"ERROR whilst processing video_id '{video_id}' - {e}")
            continue

    for url in video.get_collaborator_urls_from_description():
        if cached := Channel.query.filter(or_(Channel.url == url.lower(), Channel.forUsername == url.lower())).first():
            channel_ids.update([cached.id])
        elif lookup := Channel.from_web(url):
            channel_ids.update([lookup.id])

    return channel_ids


def get_channel_ids_from_title(video: Video) -> set:
    """
    There's no delimiter to show how many words after the @ in a video title are the actual channel title
    eg: Crocodile Rock (@Halocene ft. @Violet Orlandi @Lollia. "Violet Orlandi" is a channel name,
    but "Halocene ft." is not, the actual channel name is "Halocene"
    To accommodate this, we search for all possible combination of words that could make up
    the channel name. eg: "Halocene|Halocene ft." / "Violet|Violet Orlandi" / "Lollia"
    We assume the longest successful match is the correct one.
    """
    channel_ids = set()

    for title in video.get_collaborators_from_title():
        guest = None
        possible_titles = []

        title_words = title.split()
        for idx, word in enumerate(title_words):
            possible_titles.append(' '.join(title_words[:idx + 1]))
        possible_titles.reverse()

        for possible_title in possible_titles:
            if guest := Channel.query.filter_by(title=possible_title).first():
                break

        if not guest:
            try:
                search_results = search.from_api("|".join(possible_titles))
                guest = find_channel_by_title(search_results, possible_titles)
            except HTTPError as e:
                print(f"ERROR - Could not find channel with title '{title}' - {e}")

        if guest:
            channel_ids.update([guest.id])
        else:
            print(f"WARNING - Could not find channel with title '{title}'")

    return channel_ids


def find_channel_by_title(search_results, possible_titles):
    # Abstracted to separate method to allow return from nested loop
    for result in search_results:
        guest = Channel.from_api("id", result.result_id)
        for title_fragment in possible_titles:
            if guest.title == title_fragment:
                return guest
