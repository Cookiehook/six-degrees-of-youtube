from models.channel import ChannelPool, Channel, ChannelTypes
from models.search import Search, SearchTypes

if __name__ == '__main__':
    channel_pool = ChannelPool()

    target_name = 'Halocene'
    target_searches_list = Search.search(target_name, SearchTypes.CHANNEL)
    target_search = [s for s in target_searches_list if s.title == target_name][0]
    if not target_search:
        raise FileNotFoundError(f"Couldn't find target channel: '{target_name}'")

    target_channel = Channel.get_channel(ChannelTypes.ID, target_search.id)
    channel_pool.add(target_channel)
    print()