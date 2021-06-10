from enum import Enum

from src.models import YoutubeObject


class SearchTypes(Enum):
    CHANNEL = 'channel'
    PLAYLIST = 'playlist'
    VIDEO = 'video'


class Search(YoutubeObject):

    def __init__(self, api_response):
        if api_response['id']['kind'] == 'youtube#channel':
            self.kind = SearchTypes.CHANNEL
            self.id = api_response['id']['channelId']
            self.title = api_response['snippet']['title']
        elif api_response['id']['kind'] == "youtube#video":
            self.kind = SearchTypes.VIDEO
            self.id = api_response['id']['videoId']
            self.title = api_response['snippet']['title']
        else:
            raise NotImplemented(f"Search not implemented for {api_response['id']['kind']}")

    def __repr__(self):
        return self.title + " - " + self.kind.value + " - " + self.id

    @classmethod
    def search(cls, search_term, object_types, max_results=5):
        """

        :param search_term: Term to search by
        :param object_types: List of valid SearchType Enums
        :param max_results: Max number of results to return
        :return: Search object
        """
        params = {
            'key': cls.api_key,
            'part': 'snippet',
            'q': search_term,
            'maxResults': 5,
            'type': ",".join([t.value for t in object_types])
        }

        response = cls.get('search', params=params)
        items = response.json().get('items')
        return [cls(item) for item in items]


class SearchPool:

    _instance = None
    searches = {}

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
        return cls._instance

    def search(self, search_term, object_types: list = None):
        if not object_types:
            object_types = [SearchTypes.CHANNEL, SearchTypes.VIDEO]
        search_id = f"{search_term} - {','.join([t.value for t in object_types])}"
        if search_id not in self.searches:
            self.searches[search_id] = Search.search(search_term, object_types)
        return self.searches[search_id]
