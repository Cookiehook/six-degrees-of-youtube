import datetime

from src.models.channel import Channel
from src.models.collaboration import Collaboration
from src.models.video import Video
from tests.base_testcase import TestYoutube


class TestCollaboration(TestYoutube):

    def test_init(self):
        channel_1 = Channel('id_1', 'title_1', 'uploads_1', 'thumbnail_1', '')
        channel_2 = Channel('id_2', 'title_2', 'uploads_2', 'thumbnail_2', '')
        video = Video('video_id', 'channel_id', 'video_title', 'thumbnail', 'description', datetime.datetime.now())
        collab = Collaboration(channel_1, channel_2, video)
        assert collab.channel_1 == channel_1
        assert collab.channel_1_id == channel_1.id
        assert collab.channel_2 == channel_2
        assert collab.channel_2_id == channel_2.id
        assert collab.video == video
        assert collab.video_id == video.id

    def test_repr(self):
        channel_1 = Channel('id_1', 'title_1', 'uploads_1', 'thumbnail_1', '')
        channel_2 = Channel('id_2', 'title_2', 'uploads_2', 'thumbnail_2', '')
        video = Video('video_id', 'channel_id', 'video_title', 'thumbnail',  'description', datetime.datetime.now())
        collab = Collaboration(channel_1, channel_2, video)
        assert collab.__repr__() == 'title_1 - title_2 - video_title'

    def test_get_for_channels(self):
        c1 = Channel('1', 'title_1', 'uploads_1', 'thumb_1', '')
        c2 = Channel('2', 'title_2', 'uploads_2', 'thumb_2', '')
        c3 = Channel('3', 'title_3', 'uploads_3', 'thumb_3', '')
        c4 = Channel('4', 'title_4', 'uploads_4', 'thumb_4', '')
        c5 = Channel('5', 'title_5', 'uploads_5', 'thumb_5', '')
        v = Video('1', '', 'video_title', '', '', datetime.datetime.now())

        col_1 = Collaboration(c1, c2, v)
        col_2 = Collaboration(c1, c3, v)
        col_3 = Collaboration(c3, c2, v)
        Collaboration(c3, c5, v)
        Collaboration(c5, c4, v)
        Collaboration(c2, c4, v)

        collabs = Collaboration.for_target_channel(c1)
        assert set(collabs) == {col_1, col_2, col_3}
