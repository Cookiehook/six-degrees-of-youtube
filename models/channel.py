from enum import Enum

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
        self.uploads_playlist_id = api_response['contentDetails']['relatedPlaylists']['uploads']

    def __repr__(self):
        return f"{self.title} - {self.id}"

    def __eq__(self, other):
        if (self.id == other.id) or (self.title == other.title) or (self.url == other.url) or (self.user == other.user):
            return True
        else:
            return False

    def update(self, other):
        if other.url is not None:
            self.url = other.url
        if other.user is not None:
            self.user = other.user

    @classmethod
    def get_channel(cls, identifier_attribute: ChannelTypes, identifier_value):
        params = {
            'key': cls.api_key,
            'part': 'contentDetails,snippet',
            identifier_attribute.value: identifier_value
        }
        response = cls.get('channels', params=params)
        response.raise_for_status()
        items = response.json()['items']
        assert len(items) == 1
        if identifier_attribute == ChannelTypes.USERNAME:
            return cls(items[0], identifier_value)
        else:
            return cls(items[0], None)


class ChannelPool:

    def __init__(self):
        self.channels = []

    def __repr__(self):
        return f"({len(self.channels)}) " + ", ".join([c.title for c in self.channels])

    def add(self, identifier_attribute: ChannelTypes, identifier_value):
        for channel in self.channels:
            if identifier_attribute == ChannelTypes.ID:
                if channel.id == identifier_value:
                    return channel
            if identifier_attribute == ChannelTypes.USERNAME:
                if channel.user == identifier_value:
                    return channel
        new_channel = Channel.get_channel(identifier_attribute, identifier_value)
        self.channels.append(new_channel)
        return new_channel
