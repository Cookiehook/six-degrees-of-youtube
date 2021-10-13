from src.models.youtube_object import YoutubeObject


class SearchResult(YoutubeObject):

    def __init__(self, id, title, search_term):
        self.id = id
        self.title = title
        self.search_term = search_term

    def __repr__(self):
        return self.search_term + " - " + self.title + " - " + self.id

    @classmethod
    def from_term(cls, search_term):
        params = {
            'part': 'snippet',
            'q': search_term,
            'maxResults': 10,
            'type': 'channel'
        }

        api_items, _ = cls.get('search', params)
        results = []
        for item in api_items:
            result = cls(item['id'].get('channelId'), item['snippet']['title'], search_term)
            results.append(result)
        return results
