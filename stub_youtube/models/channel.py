from stub_youtube.extensions import db
from stub_youtube.models.json_model import JSONModel


class Channel(JSONModel):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=False)
    uploads_id = db.Column(db.String(120), unique=True, nullable=True)
    url = db.Column(db.String(120), nullable=True)
    forUsername = db.Column(db.String(120), nullable=True)

    SCHEMA = {
        'type': 'object',
        'properties': {
            'id': {'type': 'string'},
            'title': {'type': 'string'},
            'uploads': {'type': 'string'},
            'url': {'type': 'string'},
            'forUsername': {'type': 'string'},
        },
        'required': ['id', 'title', 'uploads'],
        'additionalProperties': False
    }

    def __init__(self, request_payload):
        super(Channel, self).__init__(request_payload)
        self.id = request_payload.get('id')
        self.title = request_payload.get('title')
        self.uploads_id = request_payload.get('uploads')
        self.url = request_payload.get('url')
        self.forUsername = request_payload.get('forUsername')

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'<Channel {self.title} - {self.id}>'

    def json(self):
        return {
            'id': self.id,
            'snippet': {
                'title': self.title,
                'customUrl': self.url
            },
            'contentDetails': {
                'relatedPlaylists': {
                    'uploads': self.uploads_id
                }
            }
        }
