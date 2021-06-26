from sqlalchemy import or_
from sqlalchemy.orm import relationship

from src.extensions import db
from src.models.channel import Channel
from src.models.video import Video
from src.models.youtube_object import YoutubeObject


class Collaboration(YoutubeObject):
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

    @staticmethod
    def get_for_channel(channel_id):
        return Collaboration.query.filter(or_(Collaboration.channel_1_id == channel_id, Collaboration.channel_1_id == channel_id)).all()

    def to_json(self):
        return {
            "channel_1": {
                "id": self.channel_1.id,
                "title": self.channel_1.title,
                "uploads_id": self.channel_1.uploads_id,
                "url": self.channel_1.url,
                "username": self.channel_1.username
            },
            "channel_2": {
                "id": self.channel_2.id,
                "title": self.channel_2.title,
                "uploads_id": self.channel_2.uploads_id,
                "url": self.channel_2.url,
                "username": self.channel_2.username
            },
            "video": {
                "channel_id": self.video.channel_id,
                "description": self.video.description,
                "title": self.video.title,
                "video_id": self.video.video_id,
                "published_at": self.video.published_at
            }
        }
