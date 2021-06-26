import random

import requests
from bs4 import BeautifulSoup

from src.extensions import db
from src.models.youtube_object import YoutubeObject


class Channel(YoutubeObject):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    uploads_id = db.Column(db.String, unique=True, nullable=False)
    thumbnail = db.Column(db.String, unique=True, nullable=False)
    url = db.Column(db.String)
    forUsername = db.Column(db.String)

    def __init__(self, id, title, uploads_id, thumbnail, url='', forUsername=''):
        self.id = id
        self.title = title
        self.uploads_id = uploads_id
        self.thumbnail = thumbnail
        self.url = url.lower()
        self.forUsername = forUsername.lower()

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return self.title

    @classmethod
    def from_cache(cls, identifier_attribute: str, identifier_value: str):
        filters = {
            'id': {'id': identifier_value},
            'forUsername': {'forUsername': identifier_value},
        }
        return cls.query.filter_by(**filters[identifier_attribute]).first()

    @classmethod
    def from_api(cls, identifier_attribute: str, identifier_value: str):
        if cached := cls.from_cache(identifier_attribute, identifier_value):
            return cached

        params = {
            'part': 'contentDetails,snippet',
            identifier_attribute: identifier_value
        }
        channels, _ = cls.get('channels', params)
        assert len(channels) == 1, f'Returned unexpected number of channels: {channels}'

        # If we've done a lookup by username, check if we've previously found this by ID, and update the existing
        if identifier_attribute == 'forUsername':
            if cached := Channel.query.filter_by(id=channels[0]['id']).first():
                cached.forUsername = identifier_value
                db.session.commit()
                return cached

        return cls(channels[0]['id'],
                   channels[0]['snippet']['title'],
                   channels[0]['contentDetails']['relatedPlaylists']['uploads'],
                   channels[0]['snippet']['thumbnails']['medium']['url'],
                   channels[0]['snippet'].get('customUrl', ''),
                   identifier_value if identifier_attribute == 'forUsername' else ''
                   )

    @classmethod
    def from_web(cls, url):
        print(f"Querying web for channel with URL {url}")
        # TODO - Figure out how this cookie works, and make it future proof
        response = requests.get(f'https://www.youtube.com/{url}',
                                cookies={
                                    'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(random.randint(100, 999))})

        if response.status_code == 200:
            soup = BeautifulSoup(response.content.decode(), 'html.parser')
            if og_url := soup.find('meta', property='og:url'):
                # Some URLs of the form 'youtube.com/url' are actually usernames,
                # redirecting to 'youtube.com/user/url' or 'youtube.com/c/<actual_url>'.
                # This logic ensures that we've stored this properly for future use of the cache
                if "/user/" in response.url or response.url.split("/")[-1].lower() != url.lower():
                    return cls.from_api("forUsername", response.url.split("/")[-1].lower())
                else:
                    return cls.from_api("id", og_url['content'].split("/")[-1])
            else:
                print(f"ERROR - Could not find og:url meta tag for url {url}")
        else:
            print(f"ERROR - Request responded with {response.status_code} for {url}")

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "uploads_id": self.uploads_id,
            "thumbnail": self.thumbnail,
            "url": self.url,
            "forUsername": self.forUsername
        }
