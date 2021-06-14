from src.enums import ChannelFilters
from src.models.youtube_object import YoutubeObject


class Channel(YoutubeObject):

    def __init__(self, id, title, url, uploads_id, username=None):
        self.id = id
        self.title = title
        self.url = url
        self.uploads_id = uploads_id
        self.username = username

    @classmethod
    def from_api(cls, identifier_attribute: ChannelFilters, identifier_value: str):
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
        assert len(channels) == 1, f'Returned unexpected number of channels: {channels}'
        return cls(channels[0]['id'],
                   channels[0]['snippet']['title'],
                   channels[0]['snippet'].get('customUrl'),
                   channels[0]['contentDetails']['relatedPlaylists']['uploads'],
                   identifier_value if identifier_attribute == ChannelFilters.USERNAME else None
                   )
