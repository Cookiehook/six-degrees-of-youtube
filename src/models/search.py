from src.extensions import db
from src.models.youtube_object import YoutubeObject


class SearchResult(YoutubeObject, db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    search_term = db.Column(db.String, primary_key=True)

    def __init__(self, id, title, search_term):
        self.id = id
        self.title = title
        self.search_term = search_term

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return self.search_term + " - " + self.title + " - " + self.id

    @classmethod
    def from_term(cls, search_term, cache_only=False):
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
