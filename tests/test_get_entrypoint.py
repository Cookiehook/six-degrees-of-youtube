from unittest.mock import patch, call

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
