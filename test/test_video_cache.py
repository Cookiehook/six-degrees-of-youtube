from unittest.mock import MagicMock, patch

from src.caches.video_cache import VideoCache


def test_get_from_cache_success():
    VideoCache.collection = {}
    VideoCache.collection.update({1: 'a', 2: 'b', 3: 'c'})
    video = VideoCache.get_from_cache(2)
    assert video == 'b'


def test_get_from_cache_fail():
    VideoCache.collection = {}
    VideoCache.collection.update({1: 'a', 2: 'b', 3: 'c'})
    video = VideoCache.get_from_cache(4)
    assert video is None


def test_add_to_cache_already_existing():
    VideoCache.collection = {}
    existing_video = MagicMock()
    get_mock = MagicMock()
    VideoCache.collection['123'] = existing_video
    with patch('src.models.video.Video.from_api', get_mock):
        new_video = VideoCache.add('123')
    assert new_video == existing_video
    assert get_mock.call_count == 0


def test_add_to_cache_new():
    VideoCache.collection = {}
    get_mock = MagicMock(return_value=MagicMock())
    VideoCache.collection['123'] = MagicMock()
    with patch('src.models.video.Video.from_api', get_mock):
        new_video = VideoCache.add('456')
    assert len(VideoCache.collection.keys()) == 2
    assert VideoCache.collection.get('456') == new_video
