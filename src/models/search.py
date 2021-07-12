from sqlalchemy import Column, String
from sqlalchemy.orm import Session

from src.extensions import engine
from src.models.youtube_object import YoutubeObject


class SearchResult(YoutubeObject):
    """Representation of a search result as returned from the Youtube 'search' API endpoint"""
    __tablename__ = "search_result"

    id = Column(String, primary_key=True)
    title = Column(String)
    search_term = Column(String, primary_key=True)

    def __repr__(self):
        return self.search_term + " - " + self.title + " - " + self.id

    @classmethod
    def from_term(cls, session, search_term, cache_only=False):
        """
        Retrieve a list of 10 matching search results for the given search term.
        This only retrieves results representing Channels.

        :param search_term: Term to search for
        :param cache_only: Default False. If True, only search the cache.
        :return: list of SearchResults objects or None
        """
        if cached := session.query(cls).filter(cls.search_term == search_term).all():
            return cached
        if cache_only:
            return

        params = {
            'part': 'snippet',
            'q': search_term,
            'maxResults': 10,
            'type': 'channel'
        }

        api_items, _ = cls.get('search', params)
        results = []
        for item in api_items:
            result = cls(id=item['id'].get('channelId'), title=item['snippet']['title'], search_term=search_term)
            results.append(result)
            session.add(result)
        session.commit()
        return results
