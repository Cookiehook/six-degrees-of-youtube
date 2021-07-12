from flask_sqlalchemy_session import current_session
from sqlalchemy import and_, or_, Column, Integer, String, ForeignKey, select
from sqlalchemy.orm import relationship, Session

from src.extensions import Base, engine
from src.models.channel import Channel
from src.models.video import Video


class Collaboration(Base):
    """
    Representation of a collaborative work between two channels.
    Contains both channels, and the video they collaborated on.
    """
    __tablename__ = "collaboration"

    id = Column(Integer, primary_key=True)
    channel_1_id = Column(String, ForeignKey('channel.id'))
    channel_2_id = Column(String, ForeignKey('channel.id'))
    video_id = Column(String, ForeignKey('video.id'))
    channel_1 = relationship("Channel", foreign_keys=[channel_1_id], lazy='subquery')
    channel_2 = relationship("Channel", foreign_keys=[channel_2_id], lazy='subquery')
    video = relationship("Video", backref="collaboration", lazy='subquery')

    def __init__(self, channel_1: Channel, channel_2: Channel, video: Video):
        self.channel_1 = channel_1
        self.channel_2 = channel_2
        self.video = video

        self.channel_1.id = self.channel_1.id
        self.channel_2.id = self.channel_2.id
        self.video.id = self.video.id

    def __repr__(self):
        return self.channel_1.title + " - " + self.channel_2.title + " - " + self.video.title

    def __eq__(self, other):
        return {self.channel_1, self.channel_2} == {other.channel_1, other.channel_2}

    def __hash__(self):
        c1 = self.channel_1_id if self.channel_1_id > self.channel_2_id else self.channel_2_id
        c2 = self.channel_1_id if self.channel_1_id < self.channel_2_id else self.channel_2_id
        return hash((c1, c2))

    @classmethod
    def get_collaborators(cls, target_channel: Channel) -> set:
        """
        Get all channels that have appeared in the given channel's videos

        :param target_channel: Channel instance for the target channel
        :return: list of Channel instances for collaborating partners
        """
        return set([c.channel_2 for c in current_session.query(cls).filter(cls.channel_1 == target_channel)] + [target_channel])

    @classmethod
    def for_target_channel(cls, target_channel) -> list:
        """
        Return all collaborations involving the host channel and any of the host's collaborators

        :param target_channel: Channel object for target channel
        :return: list of matching Collaboration objects.
        """
        partners = [c.id for c in cls.get_collaborators(target_channel)]
        return current_session.query(cls).filter(and_(cls.channel_1_id.in_(partners), cls.channel_2_id.in_(partners))).all()

    @classmethod
    def for_single_channel(cls, channel) -> list:
        return current_session.query(cls).filter(or_(cls.channel_1_id == channel.id, cls.channel_2_id == channel.id)).all()

    @classmethod
    def for_channels(cls, channel_1: Channel, channel_2: Channel) -> list:
        """
        Return all collaborations involving both channel IDs

        channel_1: ID of first channel to search for
        channel_2: ID of second channel to search for
        """
        query_1 = current_session.query(cls).filter(and_(cls.channel_1_id == channel_1.id, cls.channel_2_id == channel_2.id)).all()
        query_2 = current_session.query(cls).filter(and_(cls.channel_1_id == channel_2.id, cls.channel_2_id == channel_1.id)).all()
        return query_1 + query_2

    @classmethod
    def for_video(cls, video):
        return current_session.query(cls).filter(cls.video_id == video.id).all()
