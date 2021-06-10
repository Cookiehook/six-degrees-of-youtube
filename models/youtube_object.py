import os
from copy import deepcopy

import requests
from requests import HTTPError


class YoutubeObject:

    base_url = 'https://www.googleapis.com/youtube/v3/'
    api_key = os.environ['YOUTUBE_API_KEY']

    @staticmethod
    def get(endpoint, **kwargs):
        logged_args = deepcopy(kwargs)['params']
        del logged_args['key']

        print(f"Querying API for '{endpoint}' with parameters '{logged_args}")
        response = requests.get(YoutubeObject.base_url + endpoint, **kwargs)
        if response.status_code < 200 or response.status_code >= 400:
            raise HTTPError(response.json())
        if 'items' not in response.json() or len(response.json()['items']) == 0:
            raise HTTPError('API responded with no items')

        return response
