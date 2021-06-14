from copy import copy

from requests import HTTPError

from src.models.channel import ChannelPool, Channel, ChannelTypes
from src.models.collaborations import CollaborationPool
from src.models.search import SearchPool, SearchTypes
from src.models.video import VideoPool


def find_matching_title(search_results, possible_titles):
    # Abstracted to separate method to allow return from nested loop
    for result in search_results:
        guest = ChannelPool.instance().call_api(ChannelTypes.ID, result.id)
        if not guest:
            guest = Channel.call_api(ChannelTypes.ID, result.id)
        for title_fragment in possible_titles:
            if guest.title == title_fragment:
                return guest


def entrypoint():
    target_name = 'Violet Orlandi'
    target_searches_list = search_pool.call_api(target_name, [SearchTypes.CHANNEL])
    target_search = [s for s in target_searches_list if s.title == target_name][0]
    if not target_search:
        raise FileNotFoundError(f"Couldn't find target channel: '{target_name}'")

    channel_pool.add_channel(ChannelTypes.ID, target_search.id)

    iteration = 1
    while iteration <= 2:
        channel_loop = copy(channel_pool.channels)
        for host in channel_loop:
            for video in host.get_uploads():
                print(f"Parsing video '{video.title}' from '{host.title}'")

                guest_ids = video.get_collaborator_ids_from_description()
                guest_titles = video.get_collaborators_from_title()
                guest_urls = video.get_collaborator_urls_from_description()
                guest_users = video.get_collaborator_users_from_description()

                for guest_id in guest_ids:
                    print(f"Parsing Found Channel ID '{guest_id}'")
                    try:
                        if iteration == 1:
                            channel_pool.add_channel(ChannelTypes.ID, guest_id)
                        elif iteration == 2 and channel_pool.call_api(ChannelTypes.ID, guest_id):
                            collaborations.add(host, channel_pool.call_api(ChannelTypes.ID, guest_id), video)

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
                        guest_searches_list = search_pool.call_api("|".join(possible_titles), [SearchTypes.CHANNEL])
                    except HTTPError:
                        print(f"ERROR - No search results for channel named '{guest_title}'")
                        continue
                    possible_titles.reverse()
                    guest = find_matching_title(guest_searches_list, possible_titles)
                    if not guest:
                        print(f"ERROR - Couldn't find channel with title '{guest_title}'")
                        continue

                    if iteration == 1:
                        if not channel_pool.call_api(ChannelTypes.ID, guest.id):
                            channel_pool.channels.append(guest)
                    elif iteration == 2 and channel_pool.call_api(ChannelTypes.ID, guest.id):
                        collaborations.add(host, guest, video)

                for guest_url in guest_urls:
                    print(f"Parsing Found Channel URL '{guest_url}'")
                    try:
                        guest_searches_list = search_pool.call_api(guest_url)
                    except HTTPError:
                        print(f"ERROR - Couldn't find channel with URL '{guest_url}'")
                        continue

                    for result in guest_searches_list:

                        if result.kind == SearchTypes.CHANNEL and channel_pool.call_api(ChannelTypes.ID, result.id):
                            guest = channel_pool.call_api(ChannelTypes.ID, result.id)
                        else:
                            if result.kind == SearchTypes.CHANNEL:
                                guest = Channel.call_api(ChannelTypes.ID, result.id)
                            else:
                                video = video_pool.call_api(result.id)
                                guest = Channel.call_api(ChannelTypes.ID, video.channel_id)

                        if guest.url and guest.url.upper() == guest_url.upper():
                            if iteration == 1:
                                old_channel = channel_pool.call_api(ChannelTypes.ID, guest.id)
                                if old_channel:
                                    old_channel.url = guest.url
                                else:
                                    channel_pool.channels.append(guest)
                                break
                            elif iteration == 2 and channel_pool.call_api(ChannelTypes.ID, guest.id):
                                collaborations.add(host, guest, video)

                for guest_username in guest_users:
                    print(f"Parsing Found Channel Username '{guest_username}'")
                    try:
                        if iteration == 1:
                            channel_pool.add_channel(ChannelTypes.USERNAME, guest_username)
                        elif iteration == 2 and channel_pool.call_api(ChannelTypes.USERNAME, guest_username):
                            collaborations.add(host, channel_pool.call_api(ChannelTypes.USERNAME, guest_username), video)

                    except HTTPError as e:
                        if '403 Client Error' in e.args[0]:
                            raise
                        print(f"ERROR - {e}")

        iteration += 1


if __name__ == '__main__':
    entrypoint()
