import pytest
import responses
from requests import HTTPError

from src.models import youtube_object
from src.models.youtube_object import YoutubeObject

RESPONSE_ITEMS = [
        {"name": "mock-name_1"},
        {"name": "mock-name_2"},
        {"name": "mock-name_3"},
    ]


@responses.activate
def test_successful_call_without_pagination():
    youtube_object.api_keys = ['KeyOne']
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                  json={'items': RESPONSE_ITEMS},
                  status=200)

    items, next_page = YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
    assert items == RESPONSE_ITEMS
    assert next_page is None


@responses.activate
def test_successful_call_with_pagination():
    youtube_object.api_keys = ['KeyOne']
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                  json={
                      'items': RESPONSE_ITEMS,
                      'nextPageToken': 'mock-token'
                  },
                  status=200)

    items, next_page = YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
    assert items == RESPONSE_ITEMS
    assert next_page == 'mock-token'


@responses.activate
def test_failed_authentication_without_recovery():
    youtube_object.api_keys = ['KeyOne']
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                  json={"err": "mock-authentication-error"},
                  status=403)

    with pytest.raises(RuntimeError) as err:
        YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
    assert err.value.args[0] == {"err": "mock-authentication-error"}


@responses.activate
def test_failed_authentication_with_recovery():
    youtube_object.api_keys = ['KeyOne', 'KeyTwo']
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint?mock_attribute=mock_value&key=KeyOne',
                  match_querystring=True,
                  json={"err": "mock-authentication-error"},
                  status=403)
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint?mock_attribute=mock_value&key=KeyTwo',
                  match_querystring=True,
                  json={"items": RESPONSE_ITEMS},
                  status=200)

    items, _ = YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
    assert items == RESPONSE_ITEMS


@responses.activate
def test_resource_not_found():
    youtube_object.api_keys = ['KeyOne']
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                  json={"err": "mock-not-found-error"},
                  status=404)

    with pytest.raises(HTTPError) as err:
        YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
    assert err.value.args[0] == {"err": "mock-not-found-error"}


@responses.activate
def test_empty_items_response():
    youtube_object.api_keys = ['KeyOne']
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/mock-endpoint',
                  json={"items": []},
                  status=200)

    with pytest.raises(HTTPError) as err:
        YoutubeObject.get('mock-endpoint', {"mock_attribute": "mock_value"})
    assert err.value.args[0] == 'API responded with no items'
