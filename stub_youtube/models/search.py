from stub_youtube.extensions import db
from stub_youtube.models.json_model import JSONModel


class Search(JSONModel):
    type = db.Column(db.String(80), unique=False, nullable=False)
    q = db.Column(db.String(80), nullable=False)
    result_id = db.Column(db.String(80), nullable=True)

    SCHEMA = {
        'type': 'object',
        'properties': {
            'q': {'type': 'string'},
            'kind': {'type': 'string'},
            'title': {'type': 'string'},
            'id': {'type': 'string'},
        },
        'required': ['q', 'title', 'id'],
        'additionalProperties': False
    }

    def __init__(self, request_payload):
        super(Search, self).__init__(request_payload)
        self.q = request_payload['q']
        self.q = request_payload['kind']
        self.title = request_payload['title']
        self.id = request_payload['id']

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'<Search {self.type} - {self.q} - {self.id}>'

    def json(self):
        id_tag = 'channelId' if self.kind == 'channel' else 'videoId'
        return {
            'id': {
                'kind': f'youtube#{self.kind}',
                id_tag: self.id
            },
            'snippet': {
                'title': self.title
            }
        }
