from src.models.abstract_classes import Singleton


class Collaboration:

    def __init__(self, channel_1, channel_2, video):
        self.channel_1 = channel_1
        self.channel_2 = channel_2
        self.video = video

    def __repr__(self):
        return self.channel_1.title + " - " + self.channel_2.title + " - " + self.video.title


class CollaborationPool(Singleton):

    def add(self, channel_1, channel_2, video):
        if channel_1.id == channel_2.id:
            return  # Happens when an artist references another of their videos in the description
        for collab in self.collection:
            if ({channel_1.id, channel_2.id} == {collab.channel_1.id, collab.channel_2.id}) and video.id == collab.video.id:
                return  # Already recorded this video and pairing, don't repeat
        self.collection.append(Collaboration(channel_1, channel_2, video))
