from src_v3.models.video import Video


class VideoCache:
    collection = {}

    def get_from_cache(self, video_id):
        return self.collection.get(video_id)

    def add(self, video_id):
        video = self.get_from_cache(video_id)
        if not video:
            video = Video.from_api(video_id)
            self.collection[video_id] = video
        return video
