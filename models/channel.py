from enum import Enum

from models.video import Video, VideoPool
from models.youtube_object import YoutubeObject


class ChannelTypes(Enum):
    ID = 'id'
    USERNAME = 'forUsername'
    URL = 'url'


class Channel(YoutubeObject):

    def __init__(self, api_response, user):
        self.id = api_response['id']
        self.title = api_response['snippet']['title']
        self.url = api_response['snippet'].get('customUrl')
        self.user = user
        self.uploads_id = api_response['contentDetails']['relatedPlaylists']['uploads']
        self.processed = False

    def __repr__(self):
        return f"{self.title} - {self.id}"

    def get_uploads(self):
        print(f"Getting uploads for channel '{self.title}'")
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'playlistId': self.uploads_id,
            'maxResults': 50
        }

        response = self.get('playlistItems', params=params)
        all_videos = response.json()['items']

        while 'nextPageToken' in response.json():
            params['pageToken'] = response.json()['nextPageToken']
            response = self.get('playlistItems', params=params)
            all_videos.extend(response.json()['items'])

        all_videos = [Video(item) for item in all_videos]
        VideoPool.instance().videos.update({v.id: v for v in all_videos})
        return all_videos

    @classmethod
    def get_channel(cls, identifier_attribute: ChannelTypes, identifier_value):
        params = {
            'key': cls.api_key,
            'part': 'contentDetails,snippet',
            identifier_attribute.value: identifier_value
        }
        response = cls.get('channels', params=params)
        items = response.json()['items']
        if identifier_attribute == ChannelTypes.USERNAME:
            return cls(items[0], identifier_value)
        else:
            return cls(items[0], None)


class ChannelPool:

    _instance = None
    channels = []

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
        return cls._instance

    def __repr__(self):
        return f"({len(self.channels)}) " + ", ".join([c.title for c in self.channels])

    def get_channel(self, identifier_attribute: ChannelTypes, identifier_value):
        for channel in self.channels:
            if identifier_attribute == ChannelTypes.ID:
                if channel.id == identifier_value:
                    return channel
            if identifier_attribute == ChannelTypes.USERNAME:
                if channel.user and channel.user.upper() == identifier_value.upper():
                    return channel
            if identifier_attribute == ChannelTypes.URL:
                if channel.url and channel.url.upper() == identifier_value.upper():
                    return channel

    def add_channel(self, identifier_attribute: ChannelTypes, identifier_value):
        existing_channel = self.get_channel(identifier_attribute, identifier_value)
        if existing_channel:
            return existing_channel

        new_channel = Channel.get_channel(identifier_attribute, identifier_value)
        if identifier_attribute == ChannelTypes.USERNAME:
            for existing_channel in self.channels:
                if existing_channel.id == new_channel.id:
                    existing_channel.user = new_channel.user
                    return existing_channel

        self.channels.append(new_channel)
        return new_channel
