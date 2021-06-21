import datetime
import re
import unicodedata

from src_new.extensions import db
from src_new.models.channel import Channel
from src_new.models.youtube_object import YoutubeObject


class Video(YoutubeObject):
    id = db.Column(db.String, primary_key=True)
    channel_id = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    published_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, id, channel_id, title, description, published_at):
        self.id = id
        self.channel_id = channel_id
        self.title = title
        self.description = description
        self.published_at = published_at

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return self.title + " - " + self.channel_id

    def __strip_accents(self, text):
        text = unicodedata.normalize('NFD', text) \
            .encode('ascii', 'ignore') \
            .decode("utf-8")
        return str(text).strip()

    @classmethod
    def from_cache(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def from_api(cls, id):
        if cached := cls.from_cache(id):
            return cached

        params = {
            'part': 'snippet',
            'id': id,
        }

        videos, _ = cls.get('videos', params=params)
        assert len(videos) == 1, f'Returned unexpected number of videos: {videos}'

        return cls(videos[0]['id'],
                   videos[0]['snippet']['channelId'],
                   videos[0]['snippet']['title'],
                   videos[0]['snippet']['description'],
                   datetime.datetime.strptime(videos[0]['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                   )

    @classmethod
    def from_uploads(cls, channel: Channel):
        params = {
            'part': 'snippet',
            'playlistId': channel.uploads_id,
            'maxResults': 50
        }
        videos = Video.query.filter_by(channel_id=channel.id).order_by(Video.published_at.desc()).all()
        latest_video = videos[0] if videos else None
        playlist_content, next_page = cls.get('playlistItems', params)

        while True:
            for new_video in playlist_content:
                if latest_video and latest_video.id == new_video['snippet']['resourceId']['videoId']:
                    return videos
                videos.append(cls(new_video['snippet']['resourceId']['videoId'],
                                  new_video['snippet']['channelId'],
                                  new_video['snippet']['title'],
                                  new_video['snippet']['description'],
                                  datetime.datetime.strptime(new_video['snippet']['publishedAt'],
                                                             '%Y-%m-%dT%H:%M:%SZ')))
            if next_page is None:
                return videos
            params['pageToken'] = next_page
            playlist_content, next_page = cls.get('playlistItems', params)

    def to_json(self):
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "title": self.title,
            "description": self.description,
            "published_at": datetime.datetime.strftime(self.published_at, '%Y-%m-%dT%H:%M:%SZ'),
        }

    def get_collaborators_from_title(self):
        illegal_characters = ['(', ')', ',', '@ ']
        for char in illegal_characters:
            self.title = self.title.replace(char, '')

        if "@" in self.title:
            return {self.__strip_accents(s) for s in self.title.split('@')[1:]}
        return set()

    def get_collaborator_urls_from_description(self):
        match_1 = re.findall(r'youtube.com/c/([\w_\-]+)', self.description, re.UNICODE)
        match_2 = re.findall(r'youtube.com/([\w_\-]+\s)', self.description, re.UNICODE)
        return {self.__strip_accents(url) for url in match_1 + match_2}

    def get_collaborator_users_from_description(self):
        match = re.findall(r'youtube.com/user/([\w_\-]+)', self.description, re.UNICODE)
        return {self.__strip_accents(u) for u in match}

    def get_collaborator_ids_from_description(self):
        match = re.findall(r'youtube.com/channel/([a-zA-Z0-9_\-]+)', self.description)
        return {c.strip() for c in match}

    def get_video_ids_from_description(self):
        video_ids = re.findall(r'youtube.com/watch\?v=([a-zA-Z0-9_\-]+)', self.description)
        video_ids.extend(re.findall(r'youtu.be/([a-zA-Z0-9_\-]+)', self.description))
        return {v.strip() for v in video_ids}
