import re

from requests import HTTPError

from src.models import YoutubeObject


class Video(YoutubeObject):

    def __init__(self, api_response):
        if api_response['kind'] == 'youtube#playlistItem':
            self.id = api_response['snippet']['resourceId']['videoId']
        else:
            self.id = api_response['id']
        self.channel_id = api_response['snippet']['channelId']
        self.title = api_response['snippet']['title']
        self.description = api_response['snippet']['description']

    def __repr__(self):
        return self.title + " - " + self.channel_id

    @classmethod
    def get_video(cls, video_id):
        params = {
            'key': cls.api_key,
            'part': 'snippet',
            'id': video_id,
            'maxResults': 1
        }

        response = cls.get('videos', params=params)
        return cls(response.json()['items'][0])

    def get_collaborators_from_title(self):
        illegal_characters = ['(', ')', ',', '@ ']
        for char in illegal_characters:
            self.title = self.title.replace(char, '')

        if "@" in self.title and self.title[0] != "@":
            return [s.strip() for s in self.title.split('@')[1:]]
        elif "@" in self.title:
            return [s.strip() for s in self.title.split('@')]
        return []

    def get_collaborator_ids_from_description(self):
        channel_ids = re.findall('youtube.com/channel/([a-zA-Z0-9_\-]+)', self.description)
        video_ids = re.findall('youtube.com/watch\?v=([a-zA-Z0-9_\-]+)', self.description)
        video_ids.extend(re.findall('youtu.be/([a-zA-Z0-9_\-]+)', self.description))

        for video_id in video_ids:
            try:
                video = VideoPool.instance().get_video(video_id)
                channel_ids.append(video.channel_id)
            except HTTPError as e:
                print(f"ERROR - {e}")

        return channel_ids

    def get_collaborator_urls_from_description(self):
        return re.findall('youtube.com/c/([a-zA-Z0-9_\-]+)', self.description)

    def get_collaborator_users_from_description(self):
        return re.findall('youtube.com/user/([a-zA-Z0-9_\-]+)', self.description)


class VideoPool:

    _instance = None
    videos = {}

    def __init__(self):
        raise RuntimeError('Call instance() instead')


    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
        return cls._instance

    def get_video(self, video_id):
        if video_id not in self.videos:
            self.videos[video_id] = Video.get_video(video_id)
        return self.videos[video_id]

    def __repr__(self):
        return f"({len(self.videos.keys())}) "