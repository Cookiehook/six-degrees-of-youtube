from enum import Enum

from models.youtube_object import YoutubeObject


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
        else:
            raise NotImplemented(f"Search not implemented for {api_response['id']['kind']}")

    def __repr__(self):
        return self.title + " - " + self.kind.value + " - " + self.id

    @classmethod
    def search(cls, search_term, object_type: SearchTypes, max_results=5):
        """

        :param search_term: Term to search by
        :param object_type: Valid SearchType Enum
        :param max_results: Max number of results to return
        :return: Search object
        """
        params = {
            'key': cls.api_key,
            'part': 'snippet',
            'q': search_term,
            'maxResults': max_results
        }

        if object_type:
            params['type'] = object_type.value

        response = cls.get('search', params=params)
        items = response.json().get('items')
        return [cls(item) for item in items]
