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

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
        return cls._instance

    def add(self, channel_1, channel_2, video):
        for collab in self.collaborations:
            if ({channel_1, channel_2} == {collab.channel_1, collab.channel_2}) and video == collab.video:
                return  # Already recorded this collab, don't repeat
        self.collaborations.append(Collaboration(channel_1, channel_2, video))