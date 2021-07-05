from unittest import TestCase
from unittest.mock import patch, call

import responses
from requests import HTTPError

from src.controllers.exceptions import YoutubeAuthenticationException
from src.models import youtube_object
from src.models.youtube_object import YoutubeObject


class TestYoutubeObject(TestCase):
    response_items = [
        {"name": "mock-name_1"},
        {"name": "mock-name_2"},
        {"name": "mock-name_3"},
    ]

    @responses.activate
    @patch('src.models.youtube_object.logger')
    def test_successful_call_without_pagination(self, logger):
        youtube_object.api_keys = ['KeyOne']
        responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                      json={'items': self.response_items},
                      status=200)

        items, next_page = YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
        assert items == self.response_items
        assert next_page is None
        assert logger.debug.call_args_list[0] == call("Querying API with: 'mock-endpoint' - '{'mock_attribute': 'mock_value'}")

    @responses.activate
    def test_successful_call_with_pagination(self):
        youtube_object.api_keys = ['KeyOne']
        responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                      json={
                          'items': self.response_items,
                          'nextPageToken': 'mock-token'
                      },
                      status=200)

        items, next_page = YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
        assert items == self.response_items
        assert next_page == 'mock-token'

    @responses.activate
    def test_failed_authentication_without_recovery(self):
        youtube_object.api_keys = ['KeyOne']
        responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                      json={"err": "mock-authentication-error"},
                      status=403)

        with self.assertRaises(YoutubeAuthenticationException) as err:
            YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
        assert err.exception.args[0] == {"err": "mock-authentication-error"}

    @responses.activate
    @patch('src.models.youtube_object.logger')
    def test_failed_authentication_with_recovery(self, logger):
        youtube_object.api_keys = ['KeyOne', 'KeyTwo']
        responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint?mock_attribute=mock_value&key=KeyOne',
                      match_querystring=True,
                      json={"err": "mock-authentication-error"},
                      status=403)
        responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint?mock_attribute=mock_value&key=KeyTwo',
                      match_querystring=True,
                      json={"items": self.response_items},
                      status=200)

        items, _ = YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
        assert items == self.response_items
        assert logger.warning.call_args_list[0] == call("API quota limit reached, swapping key")

    @responses.activate
    def test_resource_not_found(self):
        youtube_object.api_keys = ['KeyOne']
        responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                      json={"err": "mock-not-found-error"},
                      status=404)

        with self.assertRaises(HTTPError) as err:
            YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
        assert err.exception.args[0] == {"err": "mock-not-found-error"}

    @responses.activate
    def test_empty_items_response(self):
        youtube_object.api_keys = ['KeyOne']
        responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                      json={"items": []},
                      status=200)

        with self.assertRaises(HTTPError) as err:
            YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
        assert err.exception.args[0] == 'API responded with no items'
