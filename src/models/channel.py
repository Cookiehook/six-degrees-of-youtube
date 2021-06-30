import logging

import requests
from bs4 import BeautifulSoup
from requests import HTTPError

from src.extensions import db
from src.models.url_lookup import UrlLookup
from src.models.youtube_object import YoutubeObject

logger = logging.getLogger()


class Channel(YoutubeObject, db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    uploads_id = db.Column(db.String, unique=True, nullable=False)
    thumbnail_url = db.Column(db.String, unique=True, nullable=False)
    url = db.Column(db.String)
    username = db.Column(db.String)

    def __init__(self, id, title, uploads_id, thumbnail_url, url, username=''):
        self.id = id
        self.title = title
        self.uploads_id = uploads_id
        self.thumbnail_url = thumbnail_url
        self.url = url.lower()
        self.username = username.lower()

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return self.title

    @classmethod
    def from_title(cls, title):
        return cls.query.filter_by(title=title).first()

    @classmethod
    def from_id(cls, id, cache_only=False):
        if cached := cls.query.filter_by(id=id).first():
            return cached
        if cache_only:
            return

        params = {'part': 'contentDetails,snippet', 'id': id}
        channels, _ = cls.get('channels', params)
        assert len(channels) == 1, f'Returned unexpected number of channels: {channels}'

        return cls(channels[0]['id'],
                   channels[0]['snippet']['title'],
                   channels[0]['contentDetails']['relatedPlaylists']['uploads'],
                   channels[0]['snippet']['thumbnails']['medium']['url'],
                   channels[0]['snippet'].get('customUrl', '')
                   )

    @classmethod
    def from_username(cls, username, cache_only=False):
        if cached := cls.query.filter_by(username=username).first():
            return cached
        if cache_only:
            return

        channels, _ = cls.get('channels', {'part': 'contentDetails,snippet', 'forUsername': username})
        assert len(channels) == 1, f'Returned unexpected number of channels: {channels}'

        if cached_by_id := cls.query.filter_by(id=channels[0]['id']).first():
            cached_by_id.username = username
            db.session.commit()
            return cached_by_id

        return cls(channels[0]['id'],
                   channels[0]['snippet']['title'],
                   channels[0]['contentDetails']['relatedPlaylists']['uploads'],
                   channels[0]['snippet']['thumbnails']['medium']['url'],
                   channels[0]['snippet'].get('customUrl', ''),
                   username
                   )

    @classmethod
    def from_url(cls, url, cache_only=False):
        """
        Retrieve the Channel by visiting the URL and parsing the metadata tags
        This uses requests instead of API as the only API method is to use the generic search. This
        is expensive in terms of quota usage, and not particularly accurate.
        Some URLs of the form 'youtube.com/url' are actually usernames, redirecting to 'youtube.com/user/url'
        The checking of these responses and caching of is_username allows reuse of cache

        :param url: URL to look up
        :param cache_only: default False. If True, only retrieves channels from db
        """
        if UrlLookup.url_is_username(url):
            return cls.from_username(UrlLookup.get_resolved(url))
        else:
            url = UrlLookup.get_resolved(url) or url
            if cached := cls.query.filter_by(url=url).first():
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
                    UrlLookup(url, response.url.split("/")[-1], True)
                else:
                    channel = cls.from_id(og_url['content'].split("/")[-1])
                if channel.url:
                    UrlLookup(url, channel.url)
                return channel

            else:
                raise HTTPError(f"Could not find og:url meta tag for url {url}")
        else:
            raise HTTPError(f"Request responded with {response.status_code} for {url}")
