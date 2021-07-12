import logging

import requests
from bs4 import BeautifulSoup
from flask_sqlalchemy_session import current_session
from requests import HTTPError
from sqlalchemy import Column, String, Boolean, select
from sqlalchemy.orm import Session

from src.extensions import engine
from src.models.url_lookup import UrlLookup
from src.models.youtube_object import YoutubeObject

logger = logging.getLogger()


class Channel(YoutubeObject):
    """Representation of a Channel as returned from the Youtube 'channels' API endpoint"""
    __tablename__ = "channel"

    id = Column(String, primary_key=True)
    title = Column(String)
    uploads_id = Column(String)
    thumbnail_url = Column(String)
    url = Column(String)
    username = Column(String)
    processed = Column(Boolean)

    def __repr__(self):
        return self.title

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def from_title(cls, title: str):
        """
        Queries the cache for a channel with the given title.

        :param title: Title to match, eg: 'Violet Orlandi'.
        :return: Matching Channel instance or None.
        """
        return current_session.query(cls).filter(cls.title == title).first()

    @classmethod
    def from_id(cls, id: str, cache_only: bool = False):
        """
        Queries the cache, then the API for a channel with the given ID.
        Returns matching instance or None.

        :param id: Youtube channel ID, eg: 'UCo3AxjxePfj6DHn03aiIhww'.
        :param cache_only: Default False. If True, only search the cache.
        :return: Matching Channel instance or None.
        :raises: AssertionError if more or less than 1 channel is returned from the API
        """
        if cached := current_session.get(cls, id):
            return cached
        if cache_only:
            return

        params = {'part': 'contentDetails,snippet', 'id': id}
        channels, _ = cls.get('channels', params)
        assert len(channels) == 1, f'Returned unexpected number of channels: {channels}'

        new_channel = cls(id=channels[0]['id'],
                          title=channels[0]['snippet']['title'],
                          uploads_id=channels[0]['contentDetails']['relatedPlaylists']['uploads'],
                          thumbnail_url=channels[0]['snippet']['thumbnails']['medium']['url'],
                          url=channels[0]['snippet'].get('customUrl')
                          )
        current_session.add(new_channel)
        current_session.commit()
        return new_channel

    @classmethod
    def from_username(cls, username: str, cache_only: bool = False):
        """
        Queries the cache, then the API for a channel with the given username.
        Returns matching instance or None.

        :param username: Youtube channel username, eg: 'VioletaOrlandi'.
        :param cache_only: Default False. If True, only search the cache.
        :return: Matching Channel instance or None.
        :raises: AssertionError if more or less than 1 channel is returned from the API
        """
        if cached := current_session.query(cls).filter(cls.username == username).first():
            return cached
        if cache_only:
            return

        channels, _ = cls.get('channels', {'part': 'contentDetails,snippet', 'forUsername': username})
        assert len(channels) == 1, f'Returned unexpected number of channels: {channels}'

        # Usernames are queryable, but not returned by by the API. To speed up future queries,
        # we check the cache for a channel with the ID we just retrieved, and save the username on that channel.
        if cached_by_id := current_session.get(cls, channels[0]['id']):
            cached_by_id.username = username
            current_session.commit()
            return cached_by_id

        new_channel = cls(id=channels[0]['id'],
                          title=channels[0]['snippet']['title'],
                          uploads_id=channels[0]['contentDetails']['relatedPlaylists']['uploads'],
                          thumbnail_url=channels[0]['snippet']['thumbnails']['medium']['url'],
                          url=channels[0]['snippet'].get('customUrl'),
                          username=username
                          )
        current_session.add(new_channel)
        current_session.commit()
        return new_channel

    @classmethod
    def from_url(cls, url, cache_only=False):
        """
        Queries the cache, then the web for a channel with the given url.
        Channel id is retrieved by visiting the URL and parsing the metadata tags
        This uses requests instead of API as the only API method is to use the generic search. This
        is expensive in terms of quota usage, and not particularly accurate.
        Some URLs of the form 'youtube.com/url' are actually usernames, redirecting to 'youtube.com/user/url'
        The checking of these responses and caching of is_username allows reuse of cache

        :param url: URL to look up. eg: 'VioletOrlandi'
        :param cache_only: Default False. If True, only search the cache.
        :return: Matching Channel instance or None.
        :raises: HTTPError if Youtube responds with non 200 response code, or metadata tag is not found.
        """
        if UrlLookup.url_is_username(url):
            return cls.from_username(UrlLookup.get_resolved(url), cache_only=cache_only)

        url = UrlLookup.get_resolved(url) or url
        if cached := current_session.query(cls).filter(cls.url == url).first():
            return cached
        if cache_only:
            return

        logger.debug(f"Querying web for channel with URL {url}")
        response = requests.get(f'https://www.youtube.com/{url}', cookies={'CONSENT': 'YES+GB.en-GB+V9+BX'})

        if response.status_code == 200:
            soup = BeautifulSoup(response.content.decode(), 'html.parser')
            if og_url := soup.find('meta', property='og:url'):
                if "/user/" in response.url:
                    channel = cls.from_username(response.url.split("/")[-1])
                    current_session.add(UrlLookup(original=url, resolved=response.url.split("/")[-1], is_username=True))
                else:
                    channel = cls.from_id(og_url['content'].split("/")[-1])
                    current_session.add(UrlLookup(original=url, resolved=channel.url, is_username=False))
                current_session.commit()
                return channel
            else:
                raise HTTPError(f"Could not find og:url meta tag for url {url}")
        else:
            raise HTTPError(f"Request responded with {response.status_code} for {url}")
