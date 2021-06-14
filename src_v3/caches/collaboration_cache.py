from src_v3.models.collaboration import Collaboration


class CollaborationCache:
    collection = []

    def add(self, channel_1, channel_2, video):
        if channel_1.id == channel_2.id:
            return  # Happens when an artist references another of their videos in the description
        for collab in self.collection:
            if ({channel_1.id, channel_2.id} == {collab.channel_1.id, collab.channel_2.id}) and video.id == collab.video.id:
                return  # Already recorded this video and pairing, don't repeat
        self.collection.append(Collaboration(channel_1, channel_2, video))
