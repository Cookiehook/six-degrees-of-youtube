import datetime
from unittest.mock import patch, call, MagicMock

from requests import HTTPError

from src.controllers import get_collaborations
from src.controllers.exceptions import ChannelNotFoundException
from src.models.channel import Channel
from src.models.search import SearchResult
from src.models.video import Video
from tests.base_testcase import TestYoutube


class TestGetEntrypoint(TestYoutube):

    @patch('src.controllers.get_collaborations.Channel.from_id')
    @patch('src.controllers.get_collaborations.SearchResult.from_term')
    def test_get_target_channel_success(self, from_term, from_id):
        search_term = 'Violet Orlandi'
        matching_channel = Channel('2', search_term, 'uploads', 'thumbnail', '')
        search_results = [
            SearchResult('1', 'title_1', search_term),
            SearchResult('2', search_term, search_term),
            SearchResult('3', 'title_3', search_term),
        ]
        from_term.return_value = search_results
        from_id.return_value = matching_channel
        channel = get_collaborations.get_target_channel(search_term)
        assert from_id.call_count == 1
        assert from_id.call_args_list[0] == call("2")
        assert channel == matching_channel  # Check we actually return the result of Channel.from_id

    @patch('src.controllers.get_collaborations.SearchResult.from_term')
    def test_get_target_channel_fail(self, from_term):
        search_term = 'Violet Orlandi'
        search_results = [
            SearchResult('1', 'title_1', search_term),
            SearchResult('2', 'title_2', search_term),
            SearchResult('3', 'title_3', search_term),
        ]
        from_term.return_value = search_results
        with self.assertRaises(ChannelNotFoundException) as err:
            get_collaborations.get_target_channel(search_term)
        assert err.exception.args[0] == 'Violet Orlandi'

    @patch('src.controllers.get_collaborations.logger.error')
    @patch('src.controllers.get_collaborations.Channel')
    @patch('src.controllers.get_collaborations.Video.from_id')
    def test_get_channels_from_description_success(self, patch_video_from_id, patch_channel, patch_logger):
        channel_1 = Channel('1', 'title_1', 'uploads_1', 'thumbnail_1', 'url_1')
        channel_2 = Channel('2', 'title_2', 'uploads_2', 'thumbnail_2', 'url_2')

        patch_video_from_id.return_value = MagicMock(id="123")
        patch_channel.from_id.return_value = channel_1
        patch_channel.from_username.return_value = channel_2
        patch_channel.from_url.return_value = channel_1

        video = MagicMock(
            get_channel_ids_from_description=MagicMock(return_value={"456"}),
            get_users_from_description=MagicMock(return_value={"user1", "user2"}),
            get_video_ids_from_description=MagicMock(return_value={"9", "10", "11", "12"}),
            get_urls_from_description=MagicMock(return_value={"url"})
        )
        channels = get_collaborations.get_channels_from_description(video)
        assert channels == {channel_1, channel_2}
        assert patch_video_from_id.call_count == 4
        assert patch_channel.from_id.call_count == 5
        assert patch_channel.from_username.call_count == 2
        assert patch_channel.from_url.call_count == 1
        assert patch_logger.call_count == 0

    @patch('src.controllers.get_collaborations.logger.error')
    @patch('src.controllers.get_collaborations.Channel')
    @patch('src.controllers.get_collaborations.Video.from_id')
    def test_get_channels_from_description_failures(self, patch_video_from_id, patch_channel, patch_logger):
        # ID 1 returns channel_1, ID 2 raises HTTP error for each video method
        channel_1 = Channel('1', 'title_1', 'uploads_1', 'thumbnail_1', 'url_1')

        def side_effect(arg, **kwargs):
            if arg == "1":
                return channel_1
            raise HTTPError("Test Error")

        def side_effect_video(arg, **kwargs):
            if arg == "1":
                return MagicMock(channel_id="1")
            raise HTTPError("Test Error")

        patch_video_from_id.side_effect = side_effect_video
        patch_channel.from_id.side_effect = side_effect
        patch_channel.from_username.side_effect = side_effect
        patch_channel.from_url.side_effect = side_effect

        video = MagicMock(
            get_channel_ids_from_description=MagicMock(return_value={"1", "2"}),
            get_users_from_description=MagicMock(return_value={"1", "2"}),
            get_video_ids_from_description=MagicMock(return_value={"1", "2"}),
            get_urls_from_description=MagicMock(return_value={"1", "2"}),
            __repr__=MagicMock(return_value="Test Video")
        )
        channels = get_collaborations.get_channels_from_description(video)
        assert channels == {channel_1}
        assert patch_video_from_id.call_count == 2
        assert patch_channel.from_id.call_count == 3
        assert patch_channel.from_username.call_count == 2
        assert patch_channel.from_url.call_count == 2

        assert patch_logger.call_count == 4
        assert call(
            "Failed processing channel ID '2' from video 'Test Video' - Test Error") in patch_logger.call_args_list
        assert call(
            "Failed processing username '2' from video 'Test Video' - Test Error") in patch_logger.call_args_list
        assert call(
            "Failed processing video ID '2' from video 'Test Video' - Test Error") in patch_logger.call_args_list
        assert call("Failed processing url '2' from video 'Test Video' - Test Error") in patch_logger.call_args_list

    @patch('src.controllers.get_collaborations.logger')
    @patch('src.controllers.get_collaborations.SearchResult')
    @patch('src.controllers.get_collaborations.Channel')
    def test_get_channels_from_title(self, patch_channel, patch_search, patch_logger):
        # Halocene is found by Channel.from_title on second possible title
        # Violet Orlandi is found by SearchResult.from_term, on second result, first title
        # Lollia is not found
        # h20Delir raises error during search

        halocene = Channel('id1', 'Halocene', 'uploads1', 'thumbnail1', '')
        violet_orlandi = Channel('id2', 'Violet Orlandi', 'uploads2', 'thumbnail2', '')
        searches = [SearchResult("1", "Topic - Violet Orlandi", "term"),
                    SearchResult("2", "Violet Orlandi", "term"),
                    SearchResult("3", "Topic - Violet Orlandi & Lauren Babic", "term")]

        def title_side_effect(title):
            if title == 'Halocene':
                return halocene

        def id_side_effect(id):
            if id == '2':
                return violet_orlandi
            return MagicMock()

        def search_side_effect(term, **kwargs):
            if term == 'h20Delir':
                raise HTTPError("Test Error")
            else:
                return searches

        patch_channel.from_title.side_effect = title_side_effect
        patch_channel.from_id.side_effect = id_side_effect
        patch_search.from_term.side_effect = search_side_effect
        video = MagicMock(
            __repr__=MagicMock(return_value="Test Video"),
            get_collaborators_from_title=MagicMock(return_value={'Halocene ft.', 'Violet Orlandi', 'Lollia', 'h20Delir'})
        )

        channels = get_collaborations.get_channels_from_title(video)
        assert channels == {halocene, violet_orlandi}
        assert patch_channel.from_id.call_count == 5
        assert patch_channel.from_title.call_count == 6
        assert patch_search.from_term.call_count == 3
        assert call('h20Delir', cache_only=False) in patch_search.from_term.call_args_list
        assert call('Lollia', cache_only=False) in patch_search.from_term.call_args_list
        assert call('Violet Orlandi|Violet', cache_only=False) in patch_search.from_term.call_args_list
        assert patch_logger.error.call_count == 3
        assert call("Processing channel name 'Lollia' from title of 'Test Video' failed") in patch_logger.error.call_args_list
        assert call("Processing search term '['h20Delir']' for video 'Test Video' - 'Test Error'") in patch_logger.error.call_args_list
        assert call("Processing channel name 'h20Delir' from title of 'Test Video' failed") in patch_logger.error.call_args_list

    @patch('src.controllers.get_collaborations.logger')
    @patch('src.controllers.get_collaborations.Video')
    def test_get_uploads_for_channels(self, patch_video, patch_logger):
        def side_effect(channel):
            if channel.id == 'id1':
                return [Video('1', 'id1', 'title1', 'desc', 'thumb', datetime.datetime.now()),
                        Video('2', 'id1', 'title2', 'desc', 'thumb', datetime.datetime.now())]
            elif channel.id == 'id2':
                return [Video('3', 'id2', 'title3', 'desc', 'thumb', datetime.datetime.now()),
                        Video('4', 'id2', 'title4', 'desc', 'thumb', datetime.datetime.now())]
            else:
                raise HTTPError("TestError")

        patch_video.from_channel.side_effect = side_effect
        channels = {Channel('id1', 'title1', 'uploads1', 'thumbnail1', ''),
                    Channel('id2', 'title2', 'uploads2', 'thumbnail2', ''),
                    Channel('id3', 'title3', 'uploads3', 'thumbnail3', '')}
        videos = get_collaborations.get_uploads_for_channels(channels)
        assert len(videos) == 4
        assert all([isinstance(v, str) for v in videos])
        assert patch_logger.error.call_count == 1
        assert patch_logger.error.call_args_list[0] == call("Processing uploads for channel 'title3' - 'TestError'")

    def test_distribute_videos(self):
        # Check that all videos are accounted for in distribution, regardless of list length
        for i in range(1, 1000):
            videos = []
            for j in range(1, i):
                videos.append(MagicMock())
            processes = get_collaborations.distribute_videos('1', videos)
            distributed_videos = []
            for p in processes:
                distributed_videos.extend(p._args[1])
            assert set(distributed_videos) == set(videos)

    def test_process_threads(self):
        processes = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        get_collaborations.process_threads(processes)
        for p in processes:
            assert p.start.call_count == 1
            assert p.join.call_count == 1

    @patch('src.controllers.get_collaborations.Collaboration')
    @patch('src.controllers.get_collaborations.Channel')
    @patch('src.controllers.get_collaborations.Video.from_id')
    @patch('src.controllers.get_collaborations.get_channels_from_description')
    @patch('src.controllers.get_collaborations.get_channels_from_title')
    def test_populate_collaborations(self, patch_title, patch_description, patch_video_from_id,
                                     patch_channel, patch_collaboration):
        c1 = MagicMock(id="id_1")
        c2 = MagicMock(id="id_2")
        c_host = MagicMock(id="id_host")
        patch_title.return_value = {c1}
        patch_description.return_value = {c1, c2, c_host}
        patch_channel.from_id.return_value = c_host
        get_collaborations.populate_collaborations("1", ['id1', 'id1'])

        assert patch_collaboration.call_count == 4
        assert set([call.args[0].id for call in patch_collaboration.call_args_list]) == {'id_host'}
        assert set([call.args[1].id for call in patch_collaboration.call_args_list]) == {'id_1', 'id_2'}
