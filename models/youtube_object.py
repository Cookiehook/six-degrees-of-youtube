import os

import requests


class YoutubeObject:

    base_url = 'https://www.googleapis.com/youtube/v3/'
    api_key = os.environ['YOUTUBE_API_KEY']

    @staticmethod
    def get(endpoint, **kwargs):
        return requests.get(YoutubeObject.base_url + endpoint, **kwargs)
