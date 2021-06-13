class Collaboration:

    def __init__(self, channel_1, channel_2, video):
        self.channel_1 = channel_1
        self.channel_2 = channel_2
        self.video = video

    def __repr__(self):
        return self.channel_1.title + " - " + self.channel_2.title + " - " + self.video.title


class CollaborationPool:

    _instance = None
    collaborations = []

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    def __repr__(self):
        return f"({len(self.collaborations)})"

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
        return cls._instance

    def add(self, channel_1, channel_2, video):
        if channel_1.id == channel_2.id:
            return  # Happens when an artist references another of their videos in the description
        for collab in self.collaborations:
            if ({channel_1.id, channel_2.id} == {collab.channel_1.id, collab.channel_2.id}) and video.id == collab.video.id:
                return  # Already recorded this video and pairing, don't repeat
        self.collaborations.append(Collaboration(channel_1, channel_2, video))
