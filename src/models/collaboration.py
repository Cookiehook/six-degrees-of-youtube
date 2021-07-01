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
    channel_1 = relationship("Channel", foreign_keys=[channel_1_id])
    channel_2 = relationship("Channel", foreign_keys=[channel_2_id])
    video = relationship("Video", backref="collaboration")

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

    @classmethod
    def for_channel_ids(cls, channel_ids: list) -> list:
        """
        Return all collaboration objects where both channel IDs are in the provided list.

        :param channel_ids: list of channel IDs to filter by.
        :return: list of matching Collaboration objects.
        """
        return cls.query.filter(and_(cls.channel_1_id.in_(channel_ids), cls.channel_2_id.in_(channel_ids))).all()
