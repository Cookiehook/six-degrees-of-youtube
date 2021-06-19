from src.models.channel import Channel
from src.models.video import Video


class Collaboration:

    def __init__(self, channel_1, channel_2, video):
        self.channel_1 = channel_1
        self.channel_2 = channel_2
        self.video = video

    def __repr__(self):
        return self.channel_1.title + " - " + self.channel_2.title + " - " + self.video.title

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
                "video_id": self.video.video_id
            }
        }

    @classmethod
    def from_json(cls, in_json):
        return cls(
            Channel(
                in_json['channel_1']['id'],
                in_json['channel_1']['title'],
                in_json['channel_1']['url'],
                in_json['channel_1']['uploads_id'],
                in_json['channel_1']['username'],
            ),
            Channel(
                in_json['channel_2']['id'],
                in_json['channel_2']['title'],
                in_json['channel_2']['url'],
                in_json['channel_2']['uploads_id'],
                in_json['channel_2']['username'],
            ),
            Video(
                in_json['video']['video_id'],
                in_json['video']['channel_id'],
                in_json['video']['title'],
                in_json['video']['description']
            )
        )
