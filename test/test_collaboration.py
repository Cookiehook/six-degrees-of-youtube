from unittest.mock import MagicMock

from src.models.collaboration import Collaboration


def test_constructor():
    collab = Collaboration('channel_1', 'channel_2', 'video')
    assert collab.channel_1 == 'channel_1'
    assert collab.channel_2 == 'channel_2'
    assert collab.video == 'video'


def test_repr():
    collab = Collaboration(MagicMock(title="Channel 1"), MagicMock(title="Channel 2"), MagicMock(title="Video"))
    assert collab.__repr__() == 'Channel 1 - Channel 2 - Video'
