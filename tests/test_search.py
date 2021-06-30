from unittest.mock import patch, call

from src.models.search import SearchResult
from tests.base_testcase import YoutubeTestCase


class SearchTest(YoutubeTestCase):

    def test_init(self):
        result = SearchResult('id', 'title', 'search term')
        assert result.id == 'id'
        assert result.title == 'title'
        assert result.search_term == 'search term'

    def test_repr(self):
        result = SearchResult('id', 'title', 'search term')
        assert result.__repr__() == 'search term - title - id'

    def test_from_cache_sucess(self):
        SearchResult('id_1', 'title_1', 'search-term')
        SearchResult('id_2', 'title_2', 'search-term')
        SearchResult('id_3', 'title_3', 'search-term')
        results = SearchResult.from_term('search-term', True)
        assert len(results) == 3
        assert [r.search_term for r in results] == ["search-term", "search-term", "search-term"]
        assert [r.id for r in results] == ["id_1", "id_2", "id_3"]
        assert [r.title for r in results] == ["title_1", "title_2", "title_3"]

    def test_from_cache_fail(self):
        results = SearchResult.from_term('search-term', True)
        assert results is None

    @patch('src.models.search.SearchResult.get')
    def test_from_term_api(self, patch_get):
        api_response = [
            {"id": {"channelId": "id_1"}, "snippet": {"title": "title_1"}},
            {"id": {"channelId": "id_2"}, "snippet": {"title": "title_2"}},
            {"id": {"channelId": "id_3"}, "snippet": {"title": "title_3"}},
        ]
        patch_get.return_value = api_response, None
        results = SearchResult.from_term('new-term')
        assert len(results) == 3
        assert [r.search_term for r in results] == ["new-term", "new-term", "new-term"]
        assert [r.id for r in results] == ["id_1", "id_2", "id_3"]
        assert [r.title for r in results] == ["title_1", "title_2", "title_3"]
        assert patch_get.call_args_list[0] == call('search', {'part': 'snippet', 'q': 'new-term', 'maxResults': 10, 'type': 'channel'})
