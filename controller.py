from requests import HTTPError

from models.channel import ChannelPool, Channel, ChannelTypes
from models.collaborations import CollaborationPool
from models.search import SearchPool, SearchTypes
from models.video import VideoPool


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

    target_name = 'Halocene'
    target_searches_list = search_pool.search(target_name, [SearchTypes.CHANNEL])
    target_search = [s for s in target_searches_list if s.title == target_name][0]
    if not target_search:
        raise FileNotFoundError(f"Couldn't find target channel: '{target_name}'")

    channel_pool.add_channel(ChannelTypes.ID, target_search.id)

    iterations = 0
    while iterations < 6:
        for host in channel_pool.channels:
            # Skip channels that we've already handled, but leave them in the list to allow re-use of cache
            if host.processed:
                continue

            for video in host.get_uploads():
                print(f"Parsing video '{video.title}' from '{host.title}'")

                guest_ids = video.get_collaborator_ids_from_description()
                guest_titles = video.get_collaborators_from_title()
                guest_urls = video.get_collaborator_urls_from_description()
                guest_users = video.get_collaborator_users_from_description()

                print("Parsing Found Channel IDs and Videos")
                for guest_id in guest_ids:
                    try:
                        guest = channel_pool.add_channel(ChannelTypes.ID, guest_id)
                        collaborations.add(host, guest, video)
                    except HTTPError as e:
                        print(f"ERROR - {e}")

                # There's no delimiter to show how many words after the @ in a video title are the actual channel title
                # eg: Crocodile Rock (@Halocene ft. @Violet Orlandi @Lollia. "Violet Orlandi" is a channel name,
                # but "Halocene ft." is not, the actual channel name is "Halocene"
                # To accommodate this, we search for all possible combination of words that could make up
                # the channel name. eg: "Halocene|Halocene ft." / "Violet|Violet Orlandi" / "Lollia"
                # We assume the longest successful match is the correct one.
                print("Parsing Found Channel Titles")
                for guest_title in guest_titles:
                    possible_titles = []
                    title_words = guest_title.split()
                    for idx, word in enumerate(title_words):
                        possible_titles.append(' '.join(title_words[:idx + 1]))
                    guest_searches_list = search_pool.search("|".join(possible_titles), [SearchTypes.CHANNEL], 50)
                    possible_titles.reverse()
                    guest = find_matching_title(guest_searches_list, possible_titles)
                    if not guest:
                        print(f"ERROR - Couldn't find channel with title '{guest_title}'")
                        continue
                    if not channel_pool.get_channel(ChannelTypes.ID, guest.id):
                        channel_pool.channels.append(guest)
                    collaborations.add(host, guest, video)

                print("Parsing Found Channel URLs")
                for guest_url in guest_urls:
                    guest = channel_pool.get_channel(ChannelTypes.URL, guest_url)
                    if not guest:
                        guest_searches_list = search_pool.search(target_name)
                        for result in guest_searches_list:

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

                print("Parsing Found Channel Usernames")
                for guest_username in guest_users:
                    try:
                        guest = channel_pool.add_channel(ChannelTypes.USERNAME, guest_username)
                        collaborations.add(host, guest, video)
                    except HTTPError as e:
                        print(f"ERROR - {e}")

            host.processed = True

        iterations += 1


if __name__ == '__main__':
    entrypoint()
