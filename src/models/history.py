from sqlalchemy.orm import relationship

from src.extensions import db


class History(db.Model):
    """Tracks previously searched channels and their popularity"""
    channel_id = db.Column(db.String, db.ForeignKey('channel.id'), primary_key=True)
    channel = relationship("Channel", foreign_keys=[channel_id], lazy='subquery')
    popularity = db.Column(db.Integer)

    def __init__(self, channel):
        self.channel = channel
        self.channel_id = channel.id
        self.popularity = 1

        db.session.add(self)
        db.session.commit()

    @classmethod
    def add(cls, channel):
        if old := cls.query.filter_by(channel_id=channel.id).first():
            old.popularity += 1
            db.session.commit()
        else:
            cls(channel)

    @classmethod
    def get(cls):
        return cls.query.order_by(cls.popularity.desc()).all()
