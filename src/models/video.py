import datetime
import logging
import re

from flask_sqlalchemy_session import current_session
from sqlalchemy import Column, String, DateTime

from src.models.channel import Channel
from src.models.youtube_object import YoutubeObject

logger = logging.getLogger()


class Video(YoutubeObject):
    """Representation of a Video as returned from the Youtube 'videos' API endpoint"""
    __tablename__ = "video"

    id = Column(String, primary_key=True)
    channel_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    processed_for = Column(String, default='')

    def __repr__(self):
        return self.title + " - " + self.id

    @classmethod
    def from_id(cls, id: str, cache_only: bool = False):
        """
        Queries the cache, then the API for a video with the given ID.
        Returns matching instance or None.

        :param id: Youtube channel ID, eg: 'ZUeA9_f2JTw'.
        :param cache_only: Default False. If True, only search the cache.
        :return: Matching Video instance or None.
        :raises: AssertionError if more or less than 1 video is returned from the API
        """
        if cached := current_session.query(cls).filter(cls.id == id).first():
            return cached
        if cache_only:
            return

        params = {'part': 'snippet', 'id': id}
        videos, _ = cls.get('videos', params)
        assert len(videos) == 1, f'Returned unexpected number of videos: {videos}'

        # Don't cache videos returned from individual lookups, as it breaks the ability to refresh an uploads playlist
        return cls(id=videos[0]['id'],
                   channel_id=videos[0]['snippet']['channelId'],
                   title=videos[0]['snippet']['title'],
                   description=videos[0]['snippet']['description'],
                   thumbnail_url=videos[0]['snippet']['thumbnails']['medium']['url'],
                   published_at=datetime.datetime.strptime(videos[0]['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                   )

    @classmethod
    def from_channel(cls, channel: Channel, cache_only=False):
        """
        Queries the Youtube API and retrieves a list of videos uploaded by that Channel.
        If the channel has previously been cached, then only newer unprocessed videos are returned.

        :param channel: Channel to retrieve uploads for
        :param cache_only: Default False. If true, only queries the database for videos
        :return: list of unprocessed videos
        """
        params = {
            'part': 'snippet',
            'playlistId': channel.uploads_id,
            'maxResults': 50
        }
        cached_videos = current_session.query(cls).filter(cls.channel_id == channel.id).order_by(cls.published_at.desc()).all()
        if cache_only:
            return cached_videos

        # Only omit processed videos if the channel has been successfully processed before.
        # This stops collaborations being missed if a previous processed halted due to error.
        if channel.processed:
            unprocessed_videos = current_session.query(cls).filter(cls.channel_id == channel.id, ~cls.processed_for.contains(channel.id))\
                .order_by(cls.published_at.desc()).all()
        else:
            unprocessed_videos = cached_videos

        ids = [v.id for v in cached_videos]
        latest_video = cached_videos[0] if cached_videos else None
        playlist_content, next_page = cls.get('playlistItems', params)

        while True:
            for new_video in playlist_content:
                if latest_video and latest_video.id == new_video['snippet']['resourceId']['videoId']:
                    current_session.commit()
                    return unprocessed_videos
                if new_video['snippet']['resourceId']['videoId'] in ids:
                    # Items uploaded on the same day aren't in the right order. Eg, videos at 1pm, 2pm, 3pm may come
                    # back in order 2, 3, 1. This means the 1st video isn't the newest, if the code tries to cache it,
                    # it would raise an IntegrityError as is already exists.
                    logger.warning(f"Tried to cache video {new_video['snippet']['resourceId']['videoId']} when it already exists")
                    continue

                video_instance = cls(id=new_video['snippet']['resourceId']['videoId'],
                                     channel_id=new_video['snippet']['channelId'],
                                     title=new_video['snippet']['title'],
                                     description=new_video['snippet']['description'],
                                     thumbnail_url=new_video['snippet']['thumbnails']['medium']['url'],
                                     published_at=datetime.datetime.strptime(new_video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'))
                current_session.add(video_instance)
                unprocessed_videos.append(video_instance)

            if next_page is None:
                current_session.commit()
                return unprocessed_videos
            params['pageToken'] = next_page
            playlist_content, next_page = cls.get('playlistItems', params)

    def get_collaborators_from_title(self) -> set:
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
