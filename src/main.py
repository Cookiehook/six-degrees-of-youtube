from copy import copy

from requests import HTTPError

from src.models.channel import ChannelPool, Channel, ChannelTypes
from src.models import CollaborationPool
from src.models.search import SearchPool, SearchTypes
from src.models import VideoPool


def find_matching_title(search_results, possible_titles):
    # Abstracted to separate method to allow return from nested loop
    for result in search_results:
        guest = ChannelPool.instance().get_channel(ChannelTypes.ID, result.id)
        if not guest:
            guest = Channel.get_channel(ChannelTypes.ID, result.id)
        for title_fragment in possible_titles:
            if guest.title == title_fragment:
                return guest


def entrypoint():
    channel_pool = ChannelPool.instance()
    search_pool = SearchPool.instance()
    video_pool = VideoPool.instance()
    collaborations = CollaborationPool.instance()

    target_name = 'Violet Orlandi'
    target_searches_list = search_pool.search(target_name, [SearchTypes.CHANNEL])
    target_search = [s for s in target_searches_list if s.title == target_name][0]
    if not target_search:
        raise FileNotFoundError(f"Couldn't find target channel: '{target_name}'")

    channel_pool.add_channel(ChannelTypes.ID, target_search.id)

    iterations = 1
    while iterations < 6:
        channel_loop = copy(channel_pool.channels)
        for host in channel_loop:
            # Skip channels that we've already handled, but leave them in the list to allow re-use of cache
            if host.processed:
                continue

            for video in host.get_uploads():
                print(f"Parsing video '{video.title}' from '{host.title}'")

                guest_ids = video.get_collaborator_ids_from_description()
                guest_titles = video.get_collaborators_from_title()
                guest_urls = video.get_collaborator_urls_from_description()
                guest_users = video.get_collaborator_users_from_description()

                for guest_id in guest_ids:
                    print(f"Parsing Found Channel ID '{guest_id}'")
                    try:
                        guest = channel_pool.add_channel(ChannelTypes.ID, guest_id)
                        collaborations.add(host, guest, video)
                    except HTTPError as e:
                        if '403 Client Error' in e.args[0]:
                            raise
                        print(f"ERROR - {e}")

                # There's no delimiter to show how many words after the @ in a video title are the actual channel title
                # eg: Crocodile Rock (@Halocene ft. @Violet Orlandi @Lollia. "Violet Orlandi" is a channel name,
                # but "Halocene ft." is not, the actual channel name is "Halocene"
                # To accommodate this, we search for all possible combination of words that could make up
                # the channel name. eg: "Halocene|Halocene ft." / "Violet|Violet Orlandi" / "Lollia"
                # We assume the longest successful match is the correct one.
                for guest_title in guest_titles:
                    print(f"Parsing Found Channel Title '{guest_title}'")
                    possible_titles = []
                    title_words = guest_title.split()
                    for idx, word in enumerate(title_words):
                        possible_titles.append(' '.join(title_words[:idx + 1]))
                    try:
                        guest_searches_list = search_pool.search("|".join(possible_titles), [SearchTypes.CHANNEL])
                    except HTTPError:
                        print(f"ERROR - No search results for channel named '{guest_title}'")
                        continue
                    possible_titles.reverse()
                    guest = find_matching_title(guest_searches_list, possible_titles)
                    if not guest:
                        print(f"ERROR - Couldn't find channel with title '{guest_title}'")
                        continue
                    if not channel_pool.get_channel(ChannelTypes.ID, guest.id):
                        channel_pool.channels.append(guest)
                    collaborations.add(host, guest, video)

                for guest_url in guest_urls:
                    print(f"Parsing Found Channel URL '{guest_url}'")
                    guest = channel_pool.get_channel(ChannelTypes.URL, guest_url)
                    if not guest:
                        try:
                            guest_searches_list = search_pool.search(guest_url)
                        except HTTPError:
                            print(f"ERROR - Couldn't find channel with URL '{guest_url}'")
                            continue

                        for result in guest_searches_list:

                            if guest := channel_pool.get_channel(ChannelTypes.ID, result.id):
                                pass  # We already have this channel cached, re-use it
                            else:
                                if result.kind == SearchTypes.CHANNEL:
                                    guest = Channel.get_channel(ChannelTypes.ID, result.id)
                                elif result.kind == SearchTypes.VIDEO:
                                    video = video_pool.get_video(result.id)
                                    guest = Channel.get_channel(ChannelTypes.ID, video.channel_id)

                            if guest.url == guest_url:
                                old_channel = channel_pool.get_channel(ChannelTypes.ID, guest.id)
                                if old_channel:
                                    old_channel.url = guest.url
                                else:
                                    channel_pool.channels.append(guest)
                                collaborations.add(host, guest, video)
                                break

                for guest_username in guest_users:
                    print(f"Parsing Found Channel Username '{guest_username}'")
                    try:
                        guest = channel_pool.add_channel(ChannelTypes.USERNAME, guest_username)
                        collaborations.add(host, guest, video)
                    except HTTPError as e:
                        if '403 Client Error' in e.args[0]:
                            raise
                        print(f"ERROR - {e}")

            host.processed = True

        iterations += 1


if __name__ == '__main__':
    entrypoint()
