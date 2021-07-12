import datetime

from flask_sqlalchemy_session import current_session
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship, Session

from src.extensions import Base, engine


class History(Base):
    """Tracks previously searched channels and their popularity"""
    __tablename__ = "history"

    channel_id = Column(String, ForeignKey('channel.id'), primary_key=True)
    channel = relationship("Channel", foreign_keys=[channel_id])
    popularity = Column(Integer)
    last_queried = Column(DateTime)

    def __init__(self, channel):
        self.channel_id = channel.id
        self.popularity = 1
        self.last_queried = datetime.datetime.now()

    @classmethod
    def add(cls, channel):
        if old := current_session.query(cls).filter(cls.channel_id == channel.id).first():
            old.popularity += 1
            old.last_queried = datetime.datetime.now()
        else:
            new = cls(channel)
            current_session.add(new)
        current_session.commit()

    @classmethod
    def get(cls, session):
        return current_session.query(cls).order_by(cls.popularity.desc()).limit(10).all()
