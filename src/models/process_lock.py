from flask_sqlalchemy_session import current_session
from sqlalchemy import Column, String

from src.extensions import Base


class ProcessLock(Base):
    __tablename__ = "process_lock"

    channel_name = Column(String, primary_key=True)

    @classmethod
    def get(cls, channel_name):
        return current_session.query(cls).filter(cls.channel_name == channel_name).first()

    @classmethod
    def remove(cls, channel_name):
        lock = current_session.query(cls).filter(cls.channel_name == channel_name).first()
        current_session.delete(lock)
        current_session.commit()
