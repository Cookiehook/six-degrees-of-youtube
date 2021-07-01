from unittest.mock import patch, call, MagicMock

from requests import HTTPError

from src.controllers import get_collaborations
from src.models.channel import Channel
from src.models.search import SearchResult
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
        with self.assertRaises(RuntimeError) as err:
            get_collaborations.get_target_channel(search_term)
        assert err.exception.args[0] == 'Could not find target channel: Violet Orlandi'

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

        def side_effect(arg):
            if arg == "1":
                return channel_1
            raise HTTPError("Test Error")

        def side_effect_video(arg):
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
        assert call("Failed processing channel ID '2' from video 'Test Video' - Test Error") in patch_logger.call_args_list
        assert call("Failed processing username '2' from video 'Test Video' - Test Error") in patch_logger.call_args_list
        assert call("Failed processing video ID '2' from video 'Test Video' - Test Error") in patch_logger.call_args_list
        assert call("Failed processing url '2' from video 'Test Video' - Test Error") in patch_logger.call_args_list
