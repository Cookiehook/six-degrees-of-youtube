from src.models.collaboration import Collaboration


class CollaborationCache:
    collection = []

    @classmethod
    def add(cls, channel_1, channel_2, video):
        if channel_1.id == channel_2.id:
            return  # Happens when an artist references another of their videos in the description
        for collab in cls.collection:
            if ({channel_1.id, channel_2.id} == {collab.channel_1.id, collab.channel_2.id}) and video.video_id == collab.video.video_id:
                return  # Already recorded this video and pairing, don't repeat
        cls.collection.append(Collaboration(channel_1, channel_2, video))
