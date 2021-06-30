from unittest.mock import patch, call

from src.models.url_lookup import UrlLookup
from tests.base_testcase import YoutubeTestCase


class UrlLookupTest(YoutubeTestCase):

    def setUp(self):
        super(UrlLookupTest, self).setUp()
        self.default_lookup = UrlLookup('default_original', 'default_lookup')

    @patch('src.models.url_lookup.db')
    def test_init_not_username(self, db):
        url_lookup = UrlLookup('original', 'resolved')
        assert url_lookup.original == 'original'
        assert url_lookup.resolved == 'resolved'
        assert url_lookup.is_username is False

        assert db.session.add.call_args == call(url_lookup)
        assert db.session.commit.call_count == 1

    def test_init_username(self):
        url_lookup = UrlLookup('username', 'resolved', True)
        assert url_lookup.is_username is True

    def test_repr(self):
        assert self.default_lookup.__repr__() == 'default_original - default_lookup'

    def test_get_success(self):
        cached = UrlLookup.get('default_original')
        assert cached is self.default_lookup

    def test_get_fail(self):
        cached = UrlLookup.get('unknown')
        assert cached is None

    def test_is_username_true(self):
        UrlLookup('username', 'resolved', True)
        is_username = UrlLookup.url_is_username('username')
        assert is_username is True

    def test_is_username_false(self):
        is_username = UrlLookup.url_is_username('default_original')
        assert is_username is False

    def test_is_username_none(self):
        is_username = UrlLookup.url_is_username('unknown')
        assert is_username is None
