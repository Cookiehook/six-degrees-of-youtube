from src.models.channel import Channel
from src.models.video import Video


class Collaboration:

    def __init__(self, channel_1: Channel, channel_2: Channel, video: Video):
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
                "video_id": self.video.video_id,
                "published_at": self.video.published_at
            }
        }


class CollaborationCache:
    collection = []

    @classmethod
    def add(cls, channel_1: Channel, channel_2: Channel, video: Video):
        if channel_1.id == channel_2.id:
            return  # Happens when an artist references another of their videos in the description
        for collab in cls.collection:
            if ({channel_1.id, channel_2.id} == {collab.channel_1.id, collab.channel_2.id}) and video.id == collab.video.id:
                return  # Already recorded this video and pairing, don't repeat
        cls.collection.append(Collaboration(channel_1, channel_2, video))
