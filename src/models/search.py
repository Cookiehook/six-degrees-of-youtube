from src.extensions import db
from src.models.youtube_object import YoutubeObject


class SearchResult(YoutubeObject):
    result_id = db.Column(db.String, primary_key=True)
    kind = db.Column(db.String)
    title = db.Column(db.String)
    key = db.Column(db.String, primary_key=True)

    def __init__(self, kind, result_id, title, key):
        self.kind = kind
        self.result_id = result_id
        self.title = title
        self.key = key

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return self.kind + " - " + self.title + " - " + self.result_id

    def to_json(self):
        return {
            "kind": self.kind,
            "title": self.title,
            "result_id": self.result_id,
            "key": self.key,
        }


def from_cache(search_term):
    return SearchResult.query.filter_by(key=search_term).all()


def from_api(search_term):
    if cached := from_cache(search_term):
        return cached

    params = {
        'part': 'snippet',
        'q': search_term,
        'maxResults': 5,
        'type': 'channel'
    }

    items, _ = YoutubeObject.get('search', params=params)
    return [SearchResult(item['id']['kind'],
                         item['id'].get('channelId') if item['id']['kind'] == 'youtube#channel' else item['id'].get('videoId'),
                         item['snippet']['title'],
                         search_term
                         ) for item in items]
