import datetime
import logging
import re

import requests

from src.extensions import db
from src.models.channel import Channel
from src.models.youtube_object import YoutubeObject

logger = logging.getLogger()


class Video(YoutubeObject, db.Model):
    id = db.Column(db.String, primary_key=True)
    channel_id = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    published_at = db.Column(db.DateTime, nullable=False)
    processed = db.Column(db.Boolean, nullable=False)

    def __init__(self, id: str, channel_id: str, title: str, description: str,
                 published_at: datetime.datetime, save: bool = True):
        self.id = id
        self.channel_id = channel_id
        self.title = title
        self.description = description
        self.published_at = published_at
        self.processed = False

        if save:
            db.session.add(self)
        # We do not commit after every video, as this slows down parsing of playlists
        # Instead, the from_channel method handles commits

    def __repr__(self):
        return self.title + " - " + self.channel_id

    @classmethod
    def from_id(cls, id: str, cache_only: bool = False):
        if cached := cls.query.filter_by(id=id).first():
            return cached
        if cache_only:
            return

        params = {'part': 'snippet', 'id': id}
        videos, _ = cls.get('videos', params)
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
    def from_channel(cls, channel: Channel):
        """
        Queries the Youtube API and retrieves a list of videos uploaded by that Channel.
        If the channel has previously been cached, then only newer unprocessed videos are returned.

        :param channel: Channel to retrieve uploads for
        :return: list of unprocessed videos
        """
        params = {
            'part': 'snippet',
            'playlistId': channel.uploads_id,
            'maxResults': 50
        }
        cached_videos = cls.query.filter_by(channel_id=channel.id).order_by(cls.published_at.desc()).all()
        unprocessed_videos = cls.query.filter_by(channel_id=channel.id, processed=False).order_by(cls.published_at.desc()).all()
        ids = [v.id for v in cached_videos]
        latest_video = cached_videos[0] if cached_videos else None
        playlist_content, next_page = cls.get('playlistItems', params)

        while True:
            for new_video in playlist_content:
                if latest_video and latest_video.id == new_video['snippet']['resourceId']['videoId']:
                    db.session.commit()
                    return unprocessed_videos
                if new_video['snippet']['resourceId']['videoId'] in ids:
                    # Items uploaded on the same day aren't in the right order. Eg, videos at 1pm, 2pm, 3pm may come
                    # back in order 2, 3, 1. This means the 1st video isn't the newest, if the code tries to cache it,
                    # it would raise an IntegrityError as is already exists.
                    logger.warning(f"Tried to cache video {new_video['snippet']['resourceId']['videoId']} when it already exists")
                    continue

                unprocessed_videos.append(cls(new_video['snippet']['resourceId']['videoId'],
                                              new_video['snippet']['channelId'],
                                              new_video['snippet']['title'],
                                              new_video['snippet']['description'],
                                              datetime.datetime.strptime(new_video['snippet']['publishedAt'],
                                                                         '%Y-%m-%dT%H:%M:%SZ')))
            if next_page is None:
                db.session.commit()
                return unprocessed_videos
            params['pageToken'] = next_page
            playlist_content, next_page = cls.get('playlistItems', params)

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
