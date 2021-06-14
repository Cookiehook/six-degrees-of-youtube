from unittest.mock import MagicMock, patch

from src_v3.caches.video_cache import VideoCache


def test_collection_static():
    VideoCache.collection = {}
    cache_1 = VideoCache()
    cache_1.collection.update({1: 'a', 2: 'b', 3: 'c'})

    cache_2 = VideoCache()
    assert cache_2.collection == {1: 'a', 2: 'b', 3: 'c'}


def test_get_from_cache_success():
    VideoCache.collection = {}
    cache = VideoCache()
    cache.collection.update({1: 'a', 2: 'b', 3: 'c'})
    video = cache.get_from_cache(2)
    assert video == 'b'


def test_get_from_cache_fail():
    VideoCache.collection = {}
    cache = VideoCache()
    cache.collection.update({1: 'a', 2: 'b', 3: 'c'})
    video = cache.get_from_cache(4)
    assert video is None


def test_add_to_cache_already_existing():
    VideoCache.collection = {}
    cache = VideoCache()
    existing_video = MagicMock()
    get_mock = MagicMock()
    cache.collection['123'] = existing_video
    with patch('src_v3.models.video.Video.from_api', get_mock):
        new_video = cache.add('123')
    assert new_video == existing_video
    assert get_mock.call_count == 0


def test_add_to_cache_new():
    VideoCache.collection = {}
    cache = VideoCache()
    get_mock = MagicMock(return_value=MagicMock())
    cache.collection['123'] = MagicMock()
    with patch('src_v3.models.video.Video.from_api', get_mock):
        new_video = cache.add('456')
    assert len(cache.collection.keys()) == 2
    assert cache.collection.get('456') == new_video
