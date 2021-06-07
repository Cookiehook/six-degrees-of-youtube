from enum import Enum

from models.video import Video
from models.youtube_object import YoutubeObject


class ChannelTypes(Enum):
    ID = 'id'
    USERNAME = 'forUsername'


class Channel(YoutubeObject):

    def __init__(self, api_response, user):
        self.id = api_response['id']
        self.title = api_response['snippet']['title']
        self.url = api_response['snippet'].get('customUrl')
        self.user = user
        self.videos = self.get_uploads(api_response['contentDetails']['relatedPlaylists']['uploads'])

    def __repr__(self):
        return f"{self.title} - {self.id}"

    def get_uploads(self, playlist_id):
        print(f"Getting uploads for channel '{self.title}'")
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': 50
        }

        response = self.get('playlistItems', params=params)
        all_videos = response.json()['items']

        while 'nextPageToken' in response.json():
            params['pageToken'] = response.json()['nextPageToken']
            response = self.get('playlistItems', params=params)
            all_videos.extend(response.json()['items'])

        return [Video(item) for item in all_videos]

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

    def __init__(self):
        self.channels = []

    def __repr__(self):
        return f"({len(self.channels)}) " + ", ".join([c.title for c in self.channels])

    def get_channel(self, identifier_attribute: ChannelTypes, identifier_value):
        for channel in self.channels:
            if identifier_attribute == ChannelTypes.ID:
                if channel.id == identifier_value:
                    return channel
            if identifier_attribute == ChannelTypes.USERNAME:
                if channel.user == identifier_value:
                    return channel

    def add_channel(self, identifier_attribute: ChannelTypes, identifier_value):
        existing_channel = self.get_channel(identifier_attribute, identifier_value)
        if existing_channel:
            return existing_channel

        new_channel = Channel.get_channel(identifier_attribute, identifier_value)
        self.channels.append(new_channel)
        return new_channel
