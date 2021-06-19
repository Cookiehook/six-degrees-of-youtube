from unittest.mock import MagicMock

from src.caches.collaboration_cache import CollaborationCache


def test_add_identical_artists():
    CollaborationCache.collection = []
    CollaborationCache.add(MagicMock(id='123'), MagicMock(id='123'), MagicMock(id='456'))
    assert len(CollaborationCache.collection) == 0


def test_add_existing_pairing():
    CollaborationCache.collection = []
    existing_collab = MagicMock(channel_1=MagicMock(id='123'), channel_2=MagicMock(id='456'), video=MagicMock(video_id='789'))
    CollaborationCache.collection.append(existing_collab)
    CollaborationCache.add(MagicMock(id='123'), MagicMock(id='456'), MagicMock(video_id='789'))
    assert len(CollaborationCache.collection) == 1


def test_add_new_video():
    CollaborationCache.collection = []
    existing_collab = MagicMock(channel_1=MagicMock(id='123'), channel_2=MagicMock(id='456'), video=MagicMock(id='789'))
    CollaborationCache.collection.append(existing_collab)
    CollaborationCache.add(MagicMock(id='123'), MagicMock(id='456'), MagicMock(id='100'))
    assert len(CollaborationCache.collection) == 2


def test_add_new_artists():
    CollaborationCache.collection = []
    existing_collab = MagicMock(channel_1=MagicMock(id='123'), channel_2=MagicMock(id='456'), video=MagicMock(id='789'))
    CollaborationCache.collection.append(existing_collab)
    CollaborationCache.add(MagicMock(id='123'), MagicMock(id='789'), MagicMock(id='789'))
    assert len(CollaborationCache.collection) == 2
