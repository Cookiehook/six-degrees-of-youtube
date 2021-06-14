from unittest.mock import MagicMock, patch

from src.caches.search_cache import SearchCache


def test_collection_static():
    SearchCache.collection = {}
    cache_1 = SearchCache()
    cache_1.collection.update({1: 'a', 2: 'b', 3: 'c'})

    cache_2 = SearchCache()
    assert cache_2.collection == {1: 'a', 2: 'b', 3: 'c'}


def test_get_from_cache_success():
    SearchCache.collection = {}
    cache = SearchCache()
    cache.collection.update({1: 'a', 2: 'b', 3: 'c'})
    video = cache.get_from_cache(2)
    assert video == 'b'


def test_get_from_cache_fail():
    SearchCache.collection = {}
    cache = SearchCache()
    cache.collection.update({1: 'a', 2: 'b', 3: 'c'})
    video = cache.get_from_cache(4)
    assert video is None


def test_add_to_cache_already_existing():
    SearchCache.collection = {}
    cache = SearchCache()
    existing_search = MagicMock()
    get_mock = MagicMock()
    cache.collection['123'] = existing_search
    with patch('src.models.video.Video.from_api', get_mock):
        new_video = cache.add('123', 'channel')
    assert new_video == existing_search
    assert get_mock.call_count == 0


def test_add_to_cache_new():
    SearchCache.collection = {}
    cache = SearchCache()
    get_mock = MagicMock(return_value=MagicMock())
    cache.collection['123'] = MagicMock()
    with patch('src.models.search.Search.from_api', get_mock):
        new_search = cache.add('456', 'channel')
    assert len(cache.collection.keys()) == 2
    assert cache.collection.get('456') == new_search
