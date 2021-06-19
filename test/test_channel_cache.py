from unittest.mock import MagicMock, patch

from src.caches.channel_cache import ChannelCache
from src.enums import ChannelFilters


def test_get_from_cache_id_present():
    ChannelCache.collection = []
    target_channel = MagicMock(id='id_3')
    ChannelCache.collection.extend([MagicMock(id='id_1'), MagicMock(id='id_2'), target_channel])
    channel = ChannelCache.get_from_cache(ChannelFilters.ID, 'id_3')
    assert channel is target_channel


def test_get_from_cache_id_missing():
    ChannelCache.collection = []
    ChannelCache.collection.extend([MagicMock(id='id_1'), MagicMock(id='id_2'), MagicMock(id='id_3')])
    channel = ChannelCache.get_from_cache(ChannelFilters.ID, 'id_4')
    assert channel is None


def test_get_from_cache_username_present():
    ChannelCache.collection = []
    target_channel = MagicMock(username='username_3')
    ChannelCache.collection.extend([MagicMock(username='username_1'), MagicMock(username=None), target_channel])
    channel = ChannelCache.get_from_cache(ChannelFilters.USERNAME, 'username_3')
    assert channel is target_channel


def test_get_from_cache_username_missing():
    ChannelCache.collection = []
    ChannelCache.collection.extend([MagicMock(username='username_1'), MagicMock(username=None), MagicMock(username='username_3')])
    channel = ChannelCache.get_from_cache(ChannelFilters.USERNAME, 'username_4')
    assert channel is None


def test_get_from_cache_url_present():
    ChannelCache.collection = []
    target_channel = MagicMock(url='url_3')
    ChannelCache.collection.extend([MagicMock(url='url_1'), MagicMock(username=None), target_channel])
    channel = ChannelCache.get_from_cache(ChannelFilters.URL, 'url_3')
    assert channel is target_channel


def test_get_from_cache_url_missing():
    ChannelCache.collection = []
    ChannelCache.collection.extend([MagicMock(url='url_1'), MagicMock(url=None), MagicMock(url='url_3')])
    channel = ChannelCache.get_from_cache(ChannelFilters.URL, 'url_4')
    assert channel is None


def test_add_channel_already_exists():
    ChannelCache.collection = []
    existing_channel = MagicMock(id='id')
    api_mock = MagicMock()
    ChannelCache.collection.append(existing_channel)
    with patch('src.caches.channel_cache.Channel.from_api', api_mock):
        new_channel = ChannelCache.add(ChannelFilters.ID, 'id')
    assert new_channel is existing_channel
    assert api_mock.call_count == 0


def test_add_new_channel():
    ChannelCache.collection = []
    api_mock = MagicMock(return_value='mock_channel')
    with patch('src.caches.channel_cache.Channel.from_api', api_mock):
        new_channel = ChannelCache.add(ChannelFilters.ID, 'id')
    assert new_channel == 'mock_channel'


def test_add_channel_update_username():
    ChannelCache.collection = []
    existing_channel = MagicMock(id='id', username=None)
    new_channel = MagicMock(id='id', username='new_username')
    ChannelCache.collection.append(existing_channel)

    api_mock = MagicMock(return_value=new_channel)
    with patch('src.caches.channel_cache.Channel.from_api', api_mock):
        new_channel = ChannelCache.add(ChannelFilters.USERNAME, 'id')
    assert new_channel == existing_channel
    assert existing_channel.username == 'new_username'
    assert len(ChannelCache.collection) == 1
