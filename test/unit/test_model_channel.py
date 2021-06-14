from unittest.mock import MagicMock, patch

import pytest

from src.enums import ChannelFilters
from src.models.channel import Channel, ChannelPool
from src.models.video import Video, VideoPool
from test.unit.utils import video_template

BASE_API_RESPONSE = {
    'id': 'channel_id',
    'snippet': {
        'title': 'channel_title',
        'customUrl': 'channel_url'
    },
    'contentDetails': {
        'relatedPlaylists': {
            'uploads': 'channel_uploads_id'
        }
    }
}


def test_constructor():
    channel = Channel(BASE_API_RESPONSE, 'user_name')
    assert channel.id == 'channel_id'
    assert channel.title == 'channel_title'
    assert channel.url == 'channel_url'
    assert channel.username == 'user_name'
    assert channel.uploads_id == 'channel_uploads_id'


def test_repr():
    channel = Channel(BASE_API_RESPONSE, 'user_name')
    assert channel.__repr__() == 'channel_title - channel_id'


def test_get_uploads_one_page():
    def side_effect(*args):
        return [video_template(video_id='1'), video_template(video_id='2'), video_template(video_id='3')], None

    channel = Channel(BASE_API_RESPONSE, 'user_name')
    with patch('src.models.channel.Channel.get', MagicMock(side_effect=side_effect)):
        uploads = channel.get_uploads()
    assert len(uploads) == 3
    assert len(VideoPool.instance().videos) == 3
    for idx, v in enumerate(uploads):
        assert isinstance(v, Video)
        assert v.id == str(idx + 1)


def test_get_uploads_three_pages():
    def side_effect(*args):
        if args[1].get('pageToken') is None:
            return [video_template(video_id='1'), video_template(video_id='2'), video_template(video_id='3')], 'second_page'
        if args[1].get('pageToken') == 'second_page':
            return [video_template(video_id='4'), video_template(video_id='5'), video_template(video_id='6')], 'third_page'
        elif args[1].get('pageToken') == 'third_page':
            return [video_template(video_id='7'), video_template(video_id='8'), video_template(video_id='9')], None

    channel = Channel(BASE_API_RESPONSE, 'user_name')
    with patch('src.models.channel.Channel.get', MagicMock(side_effect=side_effect)):
        uploads = channel.get_uploads()
    assert len(uploads) == 9
    assert len(VideoPool.instance().videos) == 9
    for idx, v in enumerate(uploads):
        assert isinstance(v, Video)
        assert v.id == str(idx + 1)


def test_call_api_id():
    def side_effect(*args):
        return [BASE_API_RESPONSE, ], None

    with patch('src.models.channel.Channel.get', MagicMock(side_effect=side_effect)):
        channel = Channel.call_api(ChannelFilters.ID, 'channel_id')
    assert channel.id == 'channel_id'
    assert channel.title == 'channel_title'
    assert channel.url == 'channel_url'
    assert channel.username is None
    assert channel.uploads_id == 'channel_uploads_id'


def test_call_api_username():
    def side_effect(*args):
        return [BASE_API_RESPONSE, ], None

    with patch('src.models.channel.Channel.get', MagicMock(side_effect=side_effect)):
        channel = Channel.call_api(ChannelFilters.USERNAME, 'user_name')
    assert channel.id == 'channel_id'
    assert channel.title == 'channel_title'
    assert channel.url == 'channel_url'
    assert channel.username == 'user_name'
    assert channel.uploads_id == 'channel_uploads_id'


def test_channel_pool_init():
    with pytest.raises(RuntimeError):
        ChannelPool()


def test_channel_pool_singleton():
    pool_1 = ChannelPool.instance()
    pool_2 = ChannelPool.instance()
    assert pool_1 is pool_2


def test_channel_pool_get_id_success():
    ChannelPool.reset()
    channel = Channel(BASE_API_RESPONSE)
    ChannelPool.channels.append(channel)
    new_channel = ChannelPool.instance().get_channel_from_cache(ChannelFilters.ID, 'channel_id')
    assert new_channel is channel


def test_channel_pool_get_id_fail():
    ChannelPool.reset()
    channel = Channel(BASE_API_RESPONSE)
    ChannelPool.channels.append(channel)
    new_channel = ChannelPool.instance().get_channel_from_cache(ChannelFilters.ID, 'bad_id')
    assert new_channel is None


def test_channel_pool_get_username_success():
    ChannelPool.reset()
    channel = Channel(BASE_API_RESPONSE, 'user_name')
    ChannelPool.channels.append(channel)
    new_channel = ChannelPool.instance().get_channel_from_cache(ChannelFilters.USERNAME, 'user_name')
    assert new_channel is channel


def test_channel_pool_get_username_fail():
    ChannelPool.reset()
    channel = Channel(BASE_API_RESPONSE, 'user_name')
    ChannelPool.channels.append(channel)
    new_channel = ChannelPool.instance().get_channel_from_cache(ChannelFilters.USERNAME, 'bad_name')
    assert new_channel is None


def test_channel_pool_get_url_success():
    ChannelPool.reset()
    channel = Channel(BASE_API_RESPONSE)
    ChannelPool.channels.append(channel)
    new_channel = ChannelPool.instance().get_channel_from_cache(ChannelFilters.URL, 'channel_url')
    assert new_channel is channel


def test_channel_pool_get_url_fail():
    ChannelPool.reset()
    channel = Channel(BASE_API_RESPONSE, 'user_name')
    ChannelPool.channels.append(channel)
    new_channel = ChannelPool.instance().get_channel_from_cache(ChannelFilters.URL, 'bad_url')
    assert new_channel is None


def test_add_channel_already_cached():
    ChannelPool.reset()
    channel = Channel(BASE_API_RESPONSE, 'user_name')
    ChannelPool.channels.append(channel)
    new_channel = ChannelPool.instance().add_channel(ChannelFilters.ID, 'channel_id')
    assert new_channel is channel


def test_add_channel_not_cached():
    ChannelPool.reset()
    get_mock = MagicMock(return_value=([{
        'id': 'channel_id_2',
        'snippet': {
            'title': 'channel_title_2',
            'customUrl': 'channel_url_2'
        },
        'contentDetails': {
            'relatedPlaylists': {
                'uploads': 'channel_uploads_id_2'
            }
        }
    }], None))
    channel = Channel(BASE_API_RESPONSE, 'user_name')
    ChannelPool.channels.append(channel)
    with patch('src.models.channel.Channel.get', get_mock):
        new_channel = ChannelPool.instance().add_channel(ChannelFilters.ID, 'channel_id_2')
    assert len(ChannelPool.channels) == 2
    assert new_channel.id == 'channel_id_2'


def test_add_channel_update_username():
    ChannelPool.reset()
    channel = Channel(BASE_API_RESPONSE)
    ChannelPool.channels.append(channel)
    with patch('src.models.channel.Channel.get', MagicMock(return_value=([BASE_API_RESPONSE], None))):
        new_channel = ChannelPool.instance().add_channel(ChannelFilters.USERNAME, 'username')
    assert len(ChannelPool.channels) == 1
    assert channel is new_channel
    assert channel.username == 'username'


def test_channelpool_repr():
    ChannelPool.reset()
    channel = Channel(BASE_API_RESPONSE)
    ChannelPool.channels.append(channel)
    assert ChannelPool.instance().__repr__() == '(1) channel_title'
