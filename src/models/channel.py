from src_v3.enums import ChannelFilters
from src.models.video import Video, VideoPool
from src.models.youtube_object import YoutubeObject


class Channel(YoutubeObject):

    def __init__(self, api_response: dict, username: str = None):
        """Parse required attributes from Youtube API response"""
        self.id = api_response['id']
        self.title = api_response['snippet']['title']
        self.url = api_response['snippet'].get('customUrl')
        self.username = username
        self.uploads_id = api_response['contentDetails']['relatedPlaylists']['uploads']

    def __repr__(self):
        return f"{self.title} - {self.id}"

    def get_uploads(self):
        """Get all Videos in this channel's uploads playlist"""
        print(f"Getting uploads for channel '{self.title}'")
        params = {
            'part': 'snippet',
            'playlistId': self.uploads_id,
            'maxResults': 50
        }
        all_videos, next_page = self.get('playlistItems', params)

        while next_page:
            params['pageToken'] = next_page
            page_videos, next_page = self.get('playlistItems', params)
            all_videos.extend(page_videos)

        all_videos = [Video(item) for item in all_videos]
        VideoPool.instance().videos.update({v.id: v for v in all_videos})
        return all_videos

    @classmethod
    def call_api(cls, identifier_attribute: ChannelFilters, identifier_value: str):
        """
        Retrieve channel details via Youtube API, and return a Channel object.

        :param identifier_attribute: Name of attribute to filter on (forUsername or id)
        :param identifier_value: Value of attribute to search for
        :return: Channel instance
        """
        params = {
            'part': 'contentDetails,snippet',
            identifier_attribute.value: identifier_value
        }
        channels, _ = cls.get('channels', params)
        if identifier_attribute == ChannelFilters.USERNAME:
            return cls(channels[0], identifier_value)
        else:
            return cls(channels[0])


class ChannelPool:
    _instance = None
    channels = []

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        """Return singleton instance"""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
        return cls._instance

    @staticmethod
    def reset():
        ChannelPool._instance = None
        ChannelPool.channels = []

    def __repr__(self):
        return f"({len(self.channels)}) " + ", ".join([c.title for c in self.channels])

    def get_channel_from_cache(self, identifier_attribute: ChannelFilters, identifier_value):
        """
        Return a previously retrieved Channel object with matching id, username or url.

        :param identifier_attribute: Name of attribute to compare
        :param identifier_value: Value of attribute
        :return: Channel instance or None
        """
        if identifier_attribute == ChannelFilters.ID:
            for channel in self.channels:
                # id is Base64, therefore is case-sensitive
                if channel.id == identifier_value:
                    return channel

        if identifier_attribute == ChannelFilters.USERNAME:
            for channel in self.channels:
                if channel.username and channel.username.upper() == identifier_value.upper():
                    return channel

        if identifier_attribute == ChannelFilters.URL:
            for channel in self.channels:
                if channel.url and channel.url.upper() == identifier_value.upper():
                    return channel

    def add_channel(self, identifier_attribute: ChannelFilters, identifier_value):
        """
        Checks the cache of channels, and retrieves channel from Youtube API if not found.
        Username is a filterable attribute on the API, but it not returned by the API. So if we add by
        username we check the cache for a matching channel ID and set the existing channel's username.

        :param identifier_attribute: Name of attribute to compare
        :param identifier_value: Value of attribute
        :return: Channel instance from cache or Youtube API
        """
        existing_channel = self.get_channel_from_cache(identifier_attribute, identifier_value)
        if existing_channel:
            return existing_channel

        new_channel = Channel.call_api(identifier_attribute, identifier_value)
        if identifier_attribute == ChannelFilters.USERNAME:
            for existing_channel in self.channels:
                if existing_channel.id == new_channel.id:
                    existing_channel.username = new_channel.username
                    return existing_channel

        self.channels.append(new_channel)
        return new_channel
