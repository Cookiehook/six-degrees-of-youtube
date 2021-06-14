from unittest.mock import patch, MagicMock

from src_v3.models.search import Search


def test_constructor():
    search = Search('youtube#dummy', 'id', 'title')
    assert search.kind == 'youtube#dummy'
    assert search.result_id == 'id'
    assert search.title == 'title'


def test_repr():
    search = Search('youtube#dummy', 'id', 'title')
    assert search.__repr__() == 'youtube#dummy - title - id'


def test_from_api():
    get_mock = MagicMock(return_value=([
        {"id": {"kind": "youtube#channel", "channelId": "channel_id", "title": "Channel Title"}},
        {"id": {"kind": "youtube#video", "videoId": "video_id", "title": "Video Title"}},
        {"id": {"kind": "youtube#channel", "channelId": "channel_id_2", "title": "Channel Title 2"}},
        ], None))

    with patch('src_v3.models.search.Search.get', get_mock):
        results = Search.from_api('test', 'channel,playlist')
    assert len(results) == 3
    assert results[0].kind == 'youtube#channel'
    assert results[0].result_id == 'channel_id'
    assert results[0].title == 'Channel Title'
    assert results[1].kind == 'youtube#video'
    assert results[1].result_id == 'video_id'
    assert results[1].title == 'Video Title'
    assert results[2].kind == 'youtube#channel'
    assert results[2].result_id == 'channel_id_2'
    assert results[2].title == 'Channel Title 2'
