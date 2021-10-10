import datetime
import re

from src.models.channel import Channel
from src.models.youtube_object import YoutubeObject


class Video(YoutubeObject):

    def __init__(self, id, channel_id, title, description, thumbnail_url, published_at):
        self.id = id
        self.channel_id = channel_id
        self.title = title
        self.description = description
        self.thumbnail_url = thumbnail_url
        self.published_at = published_at

    def __repr__(self):
        return f"{self.title} - {self.id}"

    @classmethod
    def from_id(cls, id: str):
        params = {'part': 'snippet', 'id': id}
        videos, _ = cls.get('videos', params)
        assert len(videos) == 1, f'Returned unexpected number of videos: {videos}'

        return cls(videos[0]['id'],
                   videos[0]['snippet']['channelId'],
                   videos[0]['snippet']['title'],
                   videos[0]['snippet']['description'],
                   videos[0]['snippet']['thumbnails'].get('medium', {}).get('url'),
                   datetime.datetime.strptime(videos[0]['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                   )

    @classmethod
    def from_channel(cls, channel: Channel):
        params = {
            'part': 'snippet',
            'playlistId': channel.uploads_id,
            'maxResults': 50
        }

        playlist_content, next_page = cls.get('playlistItems', params)
        all_videos = []
        while True:
            for new_video in playlist_content:
                video_instance = cls(new_video['snippet']['resourceId']['videoId'],
                                     new_video['snippet']['channelId'],
                                     new_video['snippet']['title'],
                                     new_video['snippet']['description'],
                                     new_video['snippet']['thumbnails'].get('medium', {}).get('url'),
                                     datetime.datetime.strptime(new_video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'))
                all_videos.append(video_instance)

            if next_page is None:
                return all_videos
            params['pageToken'] = next_page
            playlist_content, next_page = cls.get('playlistItems', params)

    def get_channel_titles_from_title(self) -> set:
        """
        Retrieve set of any tagged channels (eg: '@Violet Orlandi') from the video's title.
        A tag starts with @, but has no end delimiter. The end is assumed to be the next @
        symbol or end of string.

        :return: set of strings. eg: {'Violet Orlandi'}
        """
        illegal_characters = ['(', ')', ',', '@ ']
        for char in illegal_characters:
            self.title = self.title.replace(char, '')

        if "@" in self.title:
            return {s.strip() for s in self.title.split('@')[1:]}
        return set()

    def get_urls_from_description(self) -> set:
        """
        Retrieve any channels linked in a video description.
        The returned string is just the endpoint, not full URL. eg: 'VioletOrlandi', not 'https://youtube.com/VioletOrlandi'.
        URLs look like 'https://youtube.com/VioletOrlandi' or 'https://youtube.com/c/VioletOrlandi'
        This will miss URLs of the form youtube.com/url if they're at the very end of the description
        I have to check for trailing whitespace otherwise it identifies 'youtube.com/c' as a url, from the first pattern

        :return: set of endpoints for Youtube website. eg: {'VioletOrlandi'}
        """
        match_1 = re.findall(r'youtube.com/c/([\w_\-]+)', self.description, re.UNICODE)
        match_2 = re.findall(r'youtube.com/([\w_\-]+\s)', self.description, re.UNICODE)
        return {url.strip() for url in match_1 + match_2}

    def get_users_from_description(self) -> set:
        """
        Retrieve set of usernames from a video description.
        Usernames look like 'https://youtube/user/VioletaOrlandi'

        :return: set of usernames eg: {'VioletaOrlandi'}
        """
        match = re.findall(r'youtube.com/user/([\w_\-]+)', self.description, re.UNICODE)
        return {user.strip() for user in match}

    def get_channel_ids_from_description(self) -> set:
        """
        Retrieve set of channel IDs from a video description.
        IDs look like 'https://www.youtube.com/channel/UCo3AxjxePfj6DHn03aiIhww'

        :return: set of channel IDs. eg: {'UCo3AxjxePfj6DHn03aiIhww'}
        """
        match = re.findall(r'youtube.com/channel/([a-zA-Z0-9_\-]+)', self.description)
        return {c.strip() for c in match}

    def get_video_ids_from_description(self) -> set:
        """
        Retrieve set of video IDs from a video description.
        IDs look like 'https://www.youtube.com/watch?v=53XW1xxmmuM'

        :return: set of video IDs. eg: {'53XW1xxmmuM'}
        """

        match_1 = re.findall(r'youtube.com/watch\?v=([a-zA-Z0-9_\-]+)', self.description)
        match_2 = re.findall(r'youtu.be/([a-zA-Z0-9_\-]+)', self.description)
        return {v.strip() for v in match_1 + match_2}
