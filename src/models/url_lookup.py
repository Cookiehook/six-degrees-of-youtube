from src.extensions import db


class UrlLookup(db.Model):
    original = db.Column(db.String, primary_key=True)
    resolved = db.Column(db.String)
    is_username = db.Column(db.Boolean)

    def __init__(self, original: str, resolved: str, is_username: bool = False):
        self.original = original
        self.resolved = resolved
        self.is_username = is_username

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return self.original + " - " + self.resolved

    @classmethod
    def get(cls, url: str):
        if lookup := cls.query.filter_by(original=url).first():
            return lookup

    @staticmethod
    def url_is_username(url: str):
        if lookup := UrlLookup.query.filter_by(original=url).first():
            return lookup.is_username
