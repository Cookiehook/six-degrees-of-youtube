from unittest.mock import patch, call

import responses
from requests import HTTPError

from src.models.channel import Channel
from tests.base_testcase import TestYoutube


class TestChannel(TestYoutube):

    def setUp(self):
        super(TestChannel, self).setUp()
        self.default_channel = Channel('default_id', 'default_title', 'default_uploads_id',
                                       'default_thumbnail_url', 'default_url', 'default_username')
        self.api_response = [{
            "id": 'api_id',
            "snippet": {
                "title": "api_title",
                "customUrl": "api_url",
                "thumbnails": {
                    "medium": {
                        "url": "thumbnail_url"
                    }
                }
            },
            "contentDetails": {
                "relatedPlaylists": {
                    "uploads": "api_uploads"
                }
            }
        }]

    @patch('src.models.channel.db')
    def test_init(self, db):
        channel = Channel('id', 'title', 'uploads_id', 'thumbnail_url', 'url', 'username')
        assert channel.id == 'id'
        assert channel.title == 'title'
        assert channel.uploads_id == 'uploads_id'
        assert channel.thumbnail_url == 'thumbnail_url'
        assert channel.url == 'url'
        assert channel.username == 'username'

        assert db.session.add.call_args == call(channel)
        assert db.session.commit.call_count == 1

    def test_repr(self):
        assert self.default_channel.__repr__() == 'default_title'

    def test_known_title_from_cache(self):
        lookup = Channel.from_title('default_title')
        assert lookup is self.default_channel

    def test_unknown_title_from_cache(self):
        lookup = Channel.from_title('Unknown')
        assert lookup is None

    def test_known_id_from_cache(self):
        cached = Channel.from_id('default_id', cache_only=True)
        assert cached == self.default_channel

    def test_unknown_id_from_cache(self):
        cached = Channel.from_id('unknown_id', cache_only=True)
        assert cached is None

    def test_unknown_id_from_api_success(self):
        with patch('src.models.channel.Channel.get') as patch_get:
            patch_get.return_value = (self.api_response, None)
            lookup = Channel.from_id('unknown_id')
        assert lookup.id == self.api_response[0]['id']
        assert lookup.title == self.api_response[0]['snippet']['title']
        assert lookup.uploads_id == self.api_response[0]['contentDetails']['relatedPlaylists']['uploads']
        assert lookup.thumbnail_url == self.api_response[0]['snippet']['thumbnails']['medium']['url']
        assert lookup.url == self.api_response[0]['snippet']['customUrl']

        assert patch_get.call_args_list[0] == call('channels', {'part': 'contentDetails,snippet', 'id': 'unknown_id'})

    def test_unknown_id_from_api_multiple_channels(self):
        api_response = [{}, {}]
        with patch('src.models.channel.Channel.get') as patch_get:
            patch_get.return_value = (api_response, None)
            with self.assertRaises(AssertionError) as err:
                Channel.from_id('unknown_id')
            assert err.exception.args[0] == 'Returned unexpected number of channels: [{}, {}]'

    def test_known_username_from_cache(self):
        lookup = Channel.from_username('default_username', cache_only=True)
        assert lookup is self.default_channel

    def test_unknown_username_from_cache(self):
        lookup = Channel.from_username('Unknown', cache_only=True)
        assert lookup is None

    def test_unknown_username_from_api_success(self):
        with patch('src.models.channel.Channel.get') as patch_get:
            patch_get.return_value = (self.api_response, None)
            lookup = Channel.from_username('unknown_username')
        assert lookup.id == self.api_response[0]['id']
        assert lookup.title == self.api_response[0]['snippet']['title']
        assert lookup.uploads_id == self.api_response[0]['contentDetails']['relatedPlaylists']['uploads']
        assert lookup.thumbnail_url == self.api_response[0]['snippet']['thumbnails']['medium']['url']
        assert lookup.url == self.api_response[0]['snippet']['customUrl']
        assert lookup.username == 'unknown_username'

        assert patch_get.call_args_list[0] == call('channels', {'part': 'contentDetails,snippet', 'forUsername': 'unknown_username'})

    def test_unknown_username_from_api_update_existing(self):
        existing_channel = Channel('api_id', 'api_title', 'api_uploads_is', 'api_thumbnail_url', 'api_url')
        with patch('src.models.channel.Channel.get') as patch_get:
            patch_get.return_value = (self.api_response, None)
            lookup = Channel.from_username('unknown_username')
        assert lookup is existing_channel
        assert lookup.username == 'unknown_username'

    def test_known_url_from_cache(self):
        lookup = Channel.from_url('default_url', cache_only=True)
        assert lookup is self.default_channel

    def test_url_username_from_cache(self):
        existing_channel = Channel('id', 'title', 'uploads', 'thumbail', '', 'username')
        with patch('src.models.channel.UrlLookup') as patch_url_lookup:
            patch_url_lookup.url_is_username.return_value = True
            patch_url_lookup.get_resolved.return_value = 'username'
            lookup = Channel.from_url('username_url', cache_only=True)
        assert lookup is existing_channel
        assert patch_url_lookup.url_is_username.call_args_list[0] == call('username_url')
        assert patch_url_lookup.get_resolved.call_args_list[0] == call('username_url')

    def test_old_url_from_cache(self):
        new_channel = Channel('', '', '', '', 'new_url')
        with patch('src.models.channel.UrlLookup') as patch_url_lookup:
            patch_url_lookup.url_is_username.return_value = False
            patch_url_lookup.get_resolved.return_value = 'new_url'
            lookup = Channel.from_url('old_url', cache_only=True)
        assert lookup is new_channel

    def test_unknown_url_from_cache(self):
        lookup = Channel.from_url('unknown', cache_only=True)
        assert lookup is None

    @responses.activate
    @patch('src.models.channel.Channel.from_id')
    def test_url_lookup_from_url_success(self, from_id):
        body = b'<!DOCTYPE html><html><meta property="og:url" content="https://www.youtube.com/channel/1234567890"></html>'
        with patch('src.models.channel.UrlLookup') as patch_url_lookup:
            patch_url_lookup.url_is_username.return_value = False
            patch_url_lookup.get_resolved.return_value = None
            from_id.return_value = Channel('id', 'my-channel', 'uploads', 'thumbnail', 'new_url')

            responses.add(responses.GET, "https://www.youtube.com/unknown_url", body=body)
            lookup = Channel.from_url('unknown_url')
            assert isinstance(lookup, Channel)
            assert from_id.call_args_list[0] == call('1234567890')
            assert patch_url_lookup.call_args_list[0] == call('unknown_url', 'new_url')

    @responses.activate
    @patch('src.models.channel.Channel.from_username')
    def test_url_lookup_from_url_success_username_no_url(self, from_username):
        body = b'<!DOCTYPE html><html><meta property="og:url" content="https://www.youtube.com/channel/1234567890"></html>'
        with patch('src.models.channel.UrlLookup') as patch_url_lookup:
            patch_url_lookup.url_is_username.return_value = False
            patch_url_lookup.get_resolved.return_value = None
            from_username.return_value = Channel('id', 'my-channel', 'uploads', 'thumbnail', '')

            def response_callback(resp):
                resp.url = "https://youtube.com/user/username"
                return resp

            with responses.RequestsMock(response_callback=response_callback) as m:
                m.add(responses.GET, "https://www.youtube.com/unknown_url", body=body)
                lookup = Channel.from_url('unknown_url')

            assert isinstance(lookup, Channel)
            assert from_username.call_args_list[0] == call('username')
            assert patch_url_lookup.call_count == 1
            assert patch_url_lookup.call_args_list[0] == call('unknown_url', 'username', True)

    @responses.activate
    @patch('src.models.channel.Channel.from_username')
    def test_url_lookup_from_url_success_username_with_url(self, from_username):
        body = b'<!DOCTYPE html><html><meta property="og:url" content="https://www.youtube.com/channel/1234567890"></html>'
        with patch('src.models.channel.UrlLookup') as patch_url_lookup:
            patch_url_lookup.url_is_username.return_value = False
            patch_url_lookup.get_resolved.return_value = None
            from_username.return_value = Channel('id', 'my-channel', 'uploads', 'thumbnail', 'url')

            def response_callback(resp):
                resp.url = "https://youtube.com/user/username"
                return resp

            with responses.RequestsMock(response_callback=response_callback) as m:
                m.add(responses.GET, "https://www.youtube.com/unknown_url", body=body)
                lookup = Channel.from_url('unknown_url')

            assert isinstance(lookup, Channel)
            assert from_username.call_args_list[0] == call('username')
            assert patch_url_lookup.call_count == 2
            assert patch_url_lookup.call_args_list[0] == call('unknown_url', 'username', True)
            assert patch_url_lookup.call_args_list[1] == call('unknown_url', 'url')

    @responses.activate
    def test_url_lookup_no_meta_tag(self):
        body = b'<!DOCTYPE html><html></html>'
        with patch('src.models.channel.UrlLookup') as patch_url_lookup:
            patch_url_lookup.url_is_username.return_value = False
            patch_url_lookup.get_resolved.return_value = None
            responses.add(responses.GET, "https://www.youtube.com/unknown_url", body=body)
            with self.assertRaises(HTTPError) as err:
                Channel.from_url('unknown_url')
            assert err.exception.args[0] == 'Could not find og:url meta tag for url unknown_url'

    @responses.activate
    def test_url_lookup_non_200(self):
        with patch('src.models.channel.UrlLookup') as patch_url_lookup:
            patch_url_lookup.url_is_username.return_value = False
            patch_url_lookup.get_resolved.return_value = None
            responses.add(responses.GET, "https://www.youtube.com/unknown_url", status=404)
            with self.assertRaises(HTTPError) as err:
                Channel.from_url('unknown_url')
            assert err.exception.args[0] == 'Request responded with 404 for unknown_url'
