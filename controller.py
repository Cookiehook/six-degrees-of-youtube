from requests import HTTPError

from models.channel import ChannelPool, Channel, ChannelTypes
from models.collaborations import Collaboration
from models.search import Search, SearchTypes

if __name__ == '__main__':
    channel_pool = ChannelPool()

    target_name = 'Halocene'
    target_searches_list = Search.search(target_name, SearchTypes.CHANNEL)
    target_search = [s for s in target_searches_list if s.title == target_name][0]
    if not target_search:
        raise FileNotFoundError(f"Couldn't find target channel: '{target_name}'")

    channel_pool.add_channel(ChannelTypes.ID, target_search.id)

    collaborations = []
    iterations = 0
    while iterations < 6:
        for host in channel_pool.channels:
            for video in host.videos:
                print(f"Parsing video '{video.title}' from '{host.title}'")

                collab_ids = video.get_collaborator_ids_from_description()
                collab_titles = video.get_collaborators_from_title()
                collab_urls = video.get_collaborator_urls_from_description()
                collab_users = video.get_collaborator_users_from_description()

                print("Parsing Collab_ids")
                for guest in collab_ids:
                    try:
                        collab_channel = channel_pool.add_channel(ChannelTypes.ID, guest)
                        collaborations.append(Collaboration(host, guest, video))
                    except HTTPError as e:
                        print(f"ERROR - {e}")

                for guest in collab_titles:
                    pass  # TODO

                for guest in collab_urls:
                    pass  # TODO

                print("Parsing Collab_users")
                for guest in collab_users:
                    try:
                        collab_channel = channel_pool.add_channel(ChannelTypes.USERNAME, guest)
                        collaborations.append(Collaboration(host, guest, video))
                    except HTTPError as e:
                        print(f"ERROR - {e}")

        iterations += 1