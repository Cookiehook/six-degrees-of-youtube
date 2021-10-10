import logging

import requests
from bs4 import BeautifulSoup
from requests import HTTPError

from src.models.youtube_object import YoutubeObject

logger = logging.getLogger()


class Channel(YoutubeObject):

    def __init__(self, id, title, uploads_id, thumbnail_url, url):
        self.id = id
        self.title = title
        self.uploads_id = uploads_id
        self.thumbnail_url = thumbnail_url
        self.url = url

    def __repr__(self):
        return f"{self.title} - {self.id}"

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def from_id(cls, id: str):
        params = {'part': 'contentDetails,snippet', 'id': id}
        channels, _ = cls.get('channels', params)
        assert len(channels) == 1, f'Returned unexpected number of channels: {channels}'

        return cls(channels[0]['id'],
                   channels[0]['snippet']['title'],
                   channels[0]['contentDetails']['relatedPlaylists']['uploads'],
                   channels[0]['snippet']['thumbnails'].get('medium', {}).get('url'),
                   channels[0]['snippet'].get('customUrl')
                   )

    @classmethod
    def from_username(cls, username: str):
        channels, _ = cls.get('channels', {'part': 'contentDetails,snippet', 'forUsername': username})
        assert len(channels) == 1, f'Returned unexpected number of channels: {channels}'

        return cls(channels[0]['id'],
                   channels[0]['snippet']['title'],
                   channels[0]['contentDetails']['relatedPlaylists']['uploads'],
                   channels[0]['snippet']['thumbnails'].get('medium', {}).get('url'),
                   channels[0]['snippet'].get('customUrl')
                   )

    @classmethod
    def from_url(cls, url):
        logger.debug(f"Querying web for channel with URL {url}")
        response = requests.get(f'https://www.youtube.com/{url}', cookies={'CONSENT': 'YES+GB.en-GB+V9+BX'})

        if response.status_code == 200:
            soup = BeautifulSoup(response.content.decode(), 'html.parser')
            if og_url := soup.find('meta', property='og:url'):
                return cls.from_id(og_url['content'].split("/")[-1])
            else:
                raise HTTPError(f"Could not find og:url meta tag for url {url}")
        else:
            raise HTTPError(f"Request responded with {response.status_code} for {url}")


class ChannelCache:

    def __init__(self):
        self.__cache = set()

    def print(self):
        for channel in self.__cache:
            print(channel)

    def add(self, channel: Channel):
        self.__cache.add(channel)

    def by_id(self, channel_id):
        matches = [c for c in self.__cache if c.id == channel_id]
        if matches:
            return matches[0]

    def by_title(self, channel_title):
        matches = [c for c in self.__cache if c.title == channel_title]
        if matches:
            return matches[0]

    def by_url(self, channel_url):
        matches = [c for c in self.__cache if c.url == channel_url]
        if matches:
            return matches[0]

    def by_username(self, channel_username):
        matches = [c for c in self.__cache if c.username == channel_username]
        if matches:
            return matches[0]
