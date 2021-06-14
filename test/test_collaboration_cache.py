from unittest.mock import MagicMock

from src.caches.collaboration_cache import CollaborationCache


def test_collection_static():
    CollaborationCache.collection = []
    cache_1 = CollaborationCache()
    cache_1.collection.extend([1, 2, 3])

    cache_2 = CollaborationCache()
    assert cache_2.collection == [1, 2, 3]


def test_add_identical_artists():
    CollaborationCache.collection = []
    cache = CollaborationCache()
    cache.add(MagicMock(id='123'), MagicMock(id='123'), MagicMock(id='456'))
    assert len(cache.collection) == 0


def test_add_existing_pairing():
    CollaborationCache.collection = []
    cache = CollaborationCache()
    existing_collab = MagicMock(channel_1=MagicMock(id='123'), channel_2=MagicMock(id='456'), video=MagicMock(id='789'))
    cache.collection.append(existing_collab)
    cache.add(MagicMock(id='123'), MagicMock(id='456'), MagicMock(id='789'))
    assert len(cache.collection) == 1


def test_add_new_video():
    CollaborationCache.collection = []
    cache = CollaborationCache()
    existing_collab = MagicMock(channel_1=MagicMock(id='123'), channel_2=MagicMock(id='456'), video=MagicMock(id='789'))
    cache.collection.append(existing_collab)
    cache.add(MagicMock(id='123'), MagicMock(id='456'), MagicMock(id='100'))
    assert len(cache.collection) == 2


def test_add_new_artists():
    CollaborationCache.collection = []
    cache = CollaborationCache()
    existing_collab = MagicMock(channel_1=MagicMock(id='123'), channel_2=MagicMock(id='456'), video=MagicMock(id='789'))
    cache.collection.append(existing_collab)
    cache.add(MagicMock(id='123'), MagicMock(id='789'), MagicMock(id='789'))
    assert len(cache.collection) == 2
