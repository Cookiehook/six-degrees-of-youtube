import re

from src_v3.models.youtube_object import YoutubeObject


class Video(YoutubeObject):

    def __init__(self, video_id, channel_id, title, description):
        self.video_id = video_id
        self.channel_id = channel_id
        self.title = title
        self.description = description

    @classmethod
    def from_api(cls, video_id):
        params = {
            'part': 'snippet',
            'id': video_id,
        }

        videos, _ = cls.get('videos', params=params)
        assert len(videos) == 1, f'Returned unexpected number of videos: {videos}'

        return cls(videos[0]['id'],
                   videos[0]['snippet']['channelId'],
                   videos[0]['snippet']['title'],
                   videos[0]['snippet']['description']
                   )

    @classmethod
    def from_playlist(cls, playlist_id):
        params = {
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': 50
        }
        all_videos, next_page = cls.get('playlistItems', params)

        while next_page:
            params['pageToken'] = next_page
            page_videos, next_page = cls.get('playlistItems', params)
            all_videos.extend(page_videos)

        return [cls(video['snippet']['resourceId']['videoId'],
                    video['snippet']['channelId'],
                    video['snippet']['title'],
                    video['snippet']['description']
                    ) for video in all_videos]

    def get_collaborators_from_title(self):
        illegal_characters = ['(', ')', ',', '@ ']
        for char in illegal_characters:
            self.title = self.title.replace(char, '')

        if "@" in self.title:
            return [s.strip() for s in self.title.split('@')[1:]]
        return []

    def get_collaborator_urls_from_description(self):
        match_1 = re.findall(r'youtube.com/c/([a-zA-Z0-9_\-]+)', self.description)
        match_2 = re.findall(r'youtube.com/([a-zA-Z0-9_\-]+\s)', self.description)
        return [url.strip() for url in match_1 + match_2]

    def get_collaborator_users_from_description(self):
        match = re.findall(r'youtube.com/user/([a-zA-Z0-9_\-]+)', self.description)
        return [u.strip() for u in match]

    def get_collaborator_ids_from_description(self):
        match = re.findall(r'youtube.com/channel/([a-zA-Z0-9_\-]+)', self.description)
        return [c.strip() for c in match]

    def get_video_ids_from_description(self):
        video_ids = re.findall(r'youtube.com/watch\?v=([a-zA-Z0-9_\-]+)', self.description)
        video_ids.extend(re.findall(r'youtu.be/([a-zA-Z0-9_\-]+)', self.description))
        return [v.strip() for v in video_ids]
