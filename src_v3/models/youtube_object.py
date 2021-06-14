import os

import requests
from requests import HTTPError


class YoutubeObject:

    @staticmethod
    def get(endpoint, params):
        print(f"Querying API for '{endpoint}' with parameters '{params}")
        base_url = os.getenv('YOUTUBE_API_URL', 'https://www.googleapis.com/youtube/v3/')
        params['key'] = os.environ['YOUTUBE_API_KEY']

        response = requests.get(base_url + endpoint, params=params)
        if response.status_code < 200 or response.status_code >= 400:
            raise HTTPError(response.json())
        if 'items' not in response.json() or len(response.json()['items']) == 0:
            raise HTTPError('API responded with no items')

        return response.json().get('items'), response.json().get('nextPageToken')
