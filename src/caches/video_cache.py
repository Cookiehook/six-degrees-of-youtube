from src.models.video import Video


class VideoCache:
    collection = {}

    @classmethod
    def get_from_cache(cls, video_id) -> Video:
        return cls.collection.get(video_id)

    @classmethod
    def add(cls, video_id) -> Video:
        video = cls.get_from_cache(video_id)
        if not video:
            video = Video.from_api(video_id)
            cls.collection[video_id] = video
        return video
