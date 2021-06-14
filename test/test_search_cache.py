from unittest.mock import MagicMock, patch

from src.caches.search_cache import SearchCache


def test_get_from_cache_success():
    SearchCache.collection = {}
    SearchCache.collection.update({1: 'a', 2: 'b', 3: 'c'})
    video = SearchCache.get_from_cache(2)
    assert video == 'b'


def test_get_from_cache_fail():
    SearchCache.collection = {}
    SearchCache.collection.update({1: 'a', 2: 'b', 3: 'c'})
    video = SearchCache.get_from_cache(4)
    assert video is None


def test_add_to_cache_already_existing():
    SearchCache.collection = {}
    existing_search = MagicMock()
    get_mock = MagicMock()
    SearchCache.collection['123'] = existing_search
    with patch('src.models.video.Video.from_api', get_mock):
        new_video = SearchCache.add('123', 'channel')
    assert new_video == existing_search
    assert get_mock.call_count == 0


def test_add_to_cache_new():
    SearchCache.collection = {}
    get_mock = MagicMock(return_value=MagicMock())
    SearchCache.collection['123'] = MagicMock()
    with patch('src.models.search.Search.from_api', get_mock):
        new_search = SearchCache.add('456', 'channel')
    assert new_search is not None
    assert len(SearchCache.collection.keys()) == 2
    assert SearchCache.collection.get('456') == new_search
