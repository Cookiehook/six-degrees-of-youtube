from unittest.mock import patch, MagicMock

import pytest

from src.enums import ChannelFilters
from src.models.channel import Channel


def test_constructor_with_username():
    channel = Channel('id', 'title', 'url', 'uploads', 'username')
    assert channel.id == 'id'
    assert channel.url == 'url'
    assert channel.uploads_id == 'uploads'
    assert channel.username == 'username'


def test_constructor_without_username():
    channel = Channel('id', 'title', 'url', 'uploads')
    assert channel.id == 'id'
    assert channel.url == 'url'
    assert channel.uploads_id == 'uploads'
    assert channel.username is None


def test_from_api_with_id_success():
    get_mock = MagicMock(return_value=([{
        'id': 'channel_id',
        'snippet': {
            'title': 'Channel Title',
            'customUrl': 'channel_url'
        },
        'contentDetails': {
            'relatedPlaylists': {
                'uploads': 'uploads_id'
            }
        }
    }], None))

    with patch('src.models.channel.Channel.get', get_mock):
        channel = Channel.from_api(ChannelFilters.ID, 'channel_id')
    assert channel.id == 'channel_id'
    assert channel.title == 'Channel Title'
    assert channel.url == 'channel_url'
    assert channel.uploads_id == 'uploads_id'
    assert channel.username is None


def test_from_api_with_username_success():
    get_mock = MagicMock(return_value=([{
        'id': 'channel_id',
        'snippet': {
            'title': 'Channel Title',
            'customUrl': 'channel_url'
        },
        'contentDetails': {
            'relatedPlaylists': {
                'uploads': 'uploads_id'
            }
        }
    }], None))

    with patch('src.models.channel.Channel.get', get_mock):
        channel = Channel.from_api(ChannelFilters.USERNAME, 'username')
    assert channel.id == 'channel_id'
    assert channel.title == 'Channel Title'
    assert channel.url == 'channel_url'
    assert channel.uploads_id == 'uploads_id'
    assert channel.username == 'username'


def test_from_api_multiple_channels_fail():
    get_mock = MagicMock(return_value=([{'id': 'channel_id_1'}, {'id': 'channel_id_2'}], None))
    with patch('src.models.channel.Channel.get', get_mock):
        with pytest.raises(AssertionError) as err:
            Channel.from_api(ChannelFilters.ID, 'channel_id')
        assert err.value.args[0] == "Returned unexpected number of channels: [{'id': 'channel_id_1'}, {'id': 'channel_id_2'}]"
