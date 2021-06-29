import datetime
import re

import requests

from src.extensions import db
from src.models.youtube_object import YoutubeObject


class Video(YoutubeObject, db.Model):
    id = db.Column(db.String, primary_key=True)
    channel_id = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    published_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, id: str, channel_id: str, title: str, description: str,
                 published_at: datetime.datetime, save: bool = True):
        self.id = id
        self.channel_id = channel_id
        self.title = title
        self.description = description
        self.published_at = published_at

        if save:
            db.session.add(self)

    def __repr__(self):
        return self.title + " - " + self.channel_id

    @classmethod
    def from_id(cls, id: str, cache_only:bool = False):
        if cached := cls.query.filter_by(id=id).first():
            return cached
        if cache_only:
            return

        params = {'part': 'snippet', 'id': id}
        videos, _ = cls.get('videos', params=params)
        assert len(videos) == 1, f'Returned unexpected number of videos: {videos}'

        # Don't cache videos returned from individual lookups, as it breaks the ability to refresh an uploads playlist
        return cls(videos[0]['id'],
                   videos[0]['snippet']['channelId'],
                   videos[0]['snippet']['title'],
                   videos[0]['snippet']['description'],
                   datetime.datetime.strptime(videos[0]['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                   False
                   )

    @classmethod
    def from_uploads(cls, channel):
        raise NotImplemented

    def get_titles_from_title(self):
        illegal_characters = ['(', ')', ',', '@ ']
        for char in illegal_characters:
            self.title = self.title.replace(char, '')

        if "@" in self.title:
            return {s.strip() for s in self.title.split('@')[1:]}
        return set()

    def get_urls_from_description(self):
        # This will miss URLs of the form youtube.com/url if they're at the very end of the description
        # I have to check for trailing whitespace otherwise it identifies 'youtube.com/c' as a url,
        # from the first pattern
        self.resolve_bitly_links()
        match_1 = re.findall(r'youtube.com/c/([\w_\-]+)', self.description, re.UNICODE)
        match_2 = re.findall(r'youtube.com/([\w_\-]+\s)', self.description, re.UNICODE)
        return {url.strip() for url in match_1 + match_2}

    def get_users_from_description(self):
        self.resolve_bitly_links()
        match = re.findall(r'youtube.com/user/([\w_\-]+)', self.description, re.UNICODE)
        return {user.strip() for user in match}

    def get_channel_ids_from_description(self):
        self.resolve_bitly_links()
        match = re.findall(r'youtube.com/channel/([a-zA-Z0-9_\-]+)', self.description)
        return {c.strip() for c in match}

    def get_video_ids_from_description(self):
        self.resolve_bitly_links()
        match_1 = re.findall(r'youtube.com/watch\?v=([a-zA-Z0-9_\-]+)', self.description)
        match_2 = re.findall(r'youtu.be/([a-zA-Z0-9_\-]+)', self.description)
        return {v.strip() for v in match_1 + match_2}

    def resolve_bitly_links(self):
        """Removes bit.ly/abc123 links and appends their resolved url to the description"""
        pattern = r'http://bit.ly/[a-zA-Z0-9]+'
        bitly_links = re.findall(pattern, self.description)
        self.description = re.sub(pattern, "", self.description)
        for link in bitly_links:
            resp = requests.get(link)
            self.description += f" {resp.url} "

