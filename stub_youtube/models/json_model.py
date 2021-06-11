import jsonschema

from stub_youtube.extensions import db


class JSONModel(db.Model):

    __abstract__ = True
    SCHEMA = {}

    def __init__(self, request_payload):
        jsonschema.validate(instance=request_payload, schema=self.SCHEMA)
