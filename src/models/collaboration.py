from sqlalchemy import and_
from sqlalchemy.orm import relationship

from src.extensions import db
from src.models.channel import Channel
from src.models.video import Video


class Collaboration(db.Model):
    """
    Representation of a collaborative work between two channels.
    Contains both channels, and the video they collaborated on.
    """
    id = db.Column(db.Integer, primary_key=True)
    channel_1_id = db.Column(db.String, db.ForeignKey('channel.id'))
    channel_2_id = db.Column(db.String, db.ForeignKey('channel.id'))
    video_id = db.Column(db.String, db.ForeignKey('video.id'))
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

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return self.channel_1.title + " - " + self.channel_2.title + " - " + self.video.title

    def __eq__(self, other):
        if {self.channel_1, self.channel_2} == {other.channel_1, other.channel_2}:
            return True
        return False

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
        return set([c.channel_2 for c in cls.query.filter_by(channel_1_id=target_channel.id)] + [target_channel])

    @classmethod
    def for_target_channel(cls, target_channel) -> list:
        """
        Return all collaborations involving the host channel and any of the host's collaborators

        :param target_channel: Channel object for target channel
        :return: list of matching Collaboration objects.
        """
        partners = [c.id for c in cls.get_collaborators(target_channel)]
        return cls.query.filter(and_(cls.channel_1_id.in_(partners), cls.channel_2_id.in_(partners))).all()

    @classmethod
    def for_channels(cls, channel_1: str, channel_2: str) -> list:
        """
        Return all collaborations involving both channel IDs

        channel_1: ID of first channel to search for
        channel_2: ID of second channel to search for
        """
        query_1 = cls.query.filter(and_(cls.channel_1_id == channel_1, cls.channel_2_id == channel_2)).all()
        query_2 = cls.query.filter(and_(cls.channel_1_id == channel_2, cls.channel_2_id == channel_1)).all()
        return sorted(query_1 + query_2, key=lambda c: c.video.published_at, reverse=True)
