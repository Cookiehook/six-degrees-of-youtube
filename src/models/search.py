from src.extensions import db
from src.models.youtube_object import YoutubeObject


class SearchResult(YoutubeObject, db.Model):
    """Representation of a search result as returned from the Youtube 'search' API endpoint"""
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    search_term = db.Column(db.String, primary_key=True)

    def __init__(self, id: str, title: str, search_term: str):
        self.id = id
        self.title = title
        self.search_term = search_term

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return self.search_term + " - " + self.title + " - " + self.id

    @classmethod
    def from_term(cls, search_term, cache_only=False):
        """
        Retrieve a list of 10 matching search results for the given search term.
        This only retrieves results representing Channels.

        :param search_term: Term to search for
        :param cache_only: Default False. If True, only search the cache.
        :return: list of SearchResults objects or None
        """
        if cached := cls.query.filter_by(search_term=search_term).all():
            return cached
        if cache_only:
            return

        params = {
            'part': 'snippet',
            'q': search_term,
            'maxResults': 10,
            'type': 'channel'
        }

        items, _ = cls.get('search', params)
        return [cls(item['id'].get('channelId'),
                    item['snippet']['title'],
                    search_term
                    ) for item in items]
