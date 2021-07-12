from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session

from src.extensions import Base, engine


class ProcessLock(Base):
    __tablename__ = "process_lock"

    channel_name = Column(String, primary_key=True)

    @classmethod
    def get(cls, session, channel_name):
        return session.query(cls).filter(cls.channel_name == channel_name).first()

    @classmethod
    def remove(cls, session, channel_name):
        lock = session.query(cls).filter(cls.channel_name == channel_name).first()
        session.delete(lock)
        session.commit()
