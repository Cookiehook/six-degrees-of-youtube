from src_v3.models.youtube_object import YoutubeObject


class Search(YoutubeObject):

    def __init__(self, kind, result_id, title):
        self.kind = kind
        self.result_id = result_id
        self.title = title

    def __repr__(self):
        return self.kind + " - " + self.title + " - " + self.result_id

    @classmethod
    def from_api(cls, search_term, result_types):
        """

        :param search_term: Term to search by
        :param result_types: comma separated list of object types to search for
        :param max_results: Max number of results to return
        :return: Search object
        """
        params = {
            'part': 'snippet',
            'q': search_term,
            'maxResults': 5,
            'type': result_types
        }

        items, _ = cls.get('search', params=params)
        return [cls(item['id']['kind'],
                    item['id'].get('channelId') if item['id']['kind'] == 'youtube#channel' else item['id'].get('videoId'),
                    item['id']['title']
                    ) for item in items]
