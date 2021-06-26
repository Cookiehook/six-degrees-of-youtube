import datetime
import re
import unicodedata

from src.extensions import db
from src.models.channel import Channel
from src.models.youtube_object import YoutubeObject


class Video(YoutubeObject):
    id = db.Column(db.String, primary_key=True)
    channel_id = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    published_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, id, channel_id, title, description, published_at, save=True):
        self.id = id
        self.channel_id = channel_id
        self.title = title
        self.description = description
        self.published_at = published_at

        if save:
            db.session.add(self)

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

        # Don't cache videos returned from individual lookups, as it breaks the ability to refresh an uploads playlist
        return cls(videos[0]['id'],
                   videos[0]['snippet']['channelId'],
                   videos[0]['snippet']['title'],
                   videos[0]['snippet']['description'],
                   datetime.datetime.strptime(videos[0]['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                   False
                   )

    @classmethod
    def from_uploads(cls, channel: Channel):
        params = {
            'part': 'snippet',
            'playlistId': channel.uploads_id,
            'maxResults': 50
        }
        videos = Video.query.filter_by(channel_id=channel.id).order_by(Video.published_at.desc()).all()
        ids = [v.id for v in videos]
        latest_video = videos[0] if videos else None
        playlist_content, next_page = cls.get('playlistItems', params)

        while True:
            for new_video in playlist_content:
                if latest_video and latest_video.id == new_video['snippet']['resourceId']['videoId']:
                    db.session.commit()
                    return videos
                if new_video['snippet']['resourceId']['videoId'] in ids:
                    # Items uploaded on the same day aren't in the right order. Eg, videos at 1pm, 2pm, 3pm may come
                    # back in order 2, 3, 1. This means the 1st video isn't the newest, if the code tries to cache it,
                    # it would raise an IntegrityError as is already exists.
                    print(f"ERROR - Tried to cache video {new_video['snippet']['resourceId']['videoId']} twice")
                    continue

                videos.append(cls(new_video['snippet']['resourceId']['videoId'],
                                  new_video['snippet']['channelId'],
                                  new_video['snippet']['title'],
                                  new_video['snippet']['description'],
                                  datetime.datetime.strptime(new_video['snippet']['publishedAt'],
                                                             '%Y-%m-%dT%H:%M:%SZ')))
            if next_page is None:
                db.session.commit()
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
            return {s.strip() for s in self.title.split('@')[1:]}
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
