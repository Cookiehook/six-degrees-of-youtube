import os

import pytest
import responses
from requests import HTTPError

from src_v3.models.youtube_object import YoutubeObject


@responses.activate
def test_get_success():
    os.environ['YOUTUBE_API_KEY'] = 'DUMMY'
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/test',
                  json={'items': [1, 2, 3]}, status=200)

    items, token = YoutubeObject.get('test', {})
    assert items == [1, 2, 3]


@responses.activate
def test_get_success_with_pagination():
    os.environ['YOUTUBE_API_KEY'] = 'DUMMY'
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/test',
                  json={'items': [1, 2, 3], 'nextPageToken': 'page_token'}, status=200)

    items, token = YoutubeObject.get('test', {})
    assert items == [1, 2, 3]
    assert token == 'page_token'


@responses.activate
def test_get_http_error():
    os.environ['YOUTUBE_API_KEY'] = 'DUMMY'
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/test',
                  json={'items': [1, 2, 3]}, status=400)

    with pytest.raises(HTTPError) as err:
        YoutubeObject.get('test', {})
    assert err.value.args[0] == {'items': [1, 2, 3]}


@responses.activate
def test_get_no_items():
    os.environ['YOUTUBE_API_KEY'] = 'DUMMY'
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/test',
                  json={'message': 'whatwhat?'}, status=200)

    with pytest.raises(HTTPError) as err:
        YoutubeObject.get('test', {})
    assert err.value.args[0] == 'API responded with no items'


@responses.activate
def test_get_empty_items():
    os.environ['YOUTUBE_API_KEY'] = 'DUMMY'
    responses.add(responses.GET, 'https://www.googleapis.com/youtube/v3/test',
                  json={'items': []}, status=200)

    with pytest.raises(HTTPError) as err:
        YoutubeObject.get('test', {})
    assert err.value.args[0] == 'API responded with no items'
