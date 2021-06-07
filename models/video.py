import re

from requests import HTTPError

from models.youtube_object import YoutubeObject


class Video(YoutubeObject):

    def __init__(self, api_response):
        self.id = api_response['snippet']['resourceId']['videoId']
        self.channel_id = api_response['snippet']['channelId']
        self.title = api_response['snippet']['title']
        self.description = api_response['snippet']['description']

    def __repr__(self):
        return self.title + " - " + self.channel_id

    def get_collaborators_from_title(self):
        illegal_characters = ['(', ')', ',']
        for char in illegal_characters:
            self.title = self.title.replace(char, '')

        if "@" in self.title and self.title[0] != "@":
            return [s.strip() for s in self.title.split('@')[1:]]
        elif "@" in self.title:
            return [s.strip() for s in self.title.split('@')]
        return []

    def get_collaborator_ids_from_description(self):
        channel_ids = re.findall('youtube.com/channel/([a-zA-Z0-9_\-]+)', self.description)
        video_ids = re.findall('youtube.com/watch\?v=([a-zA-Z0-9_\-]+)', self.description)

        for video_id in video_ids:
            try:
                params = {
                    'key': self.api_key,
                    'part': 'snippet',
                    'id': video_id,
                    'maxResults': 1
                }

                response = self.get('videos', params=params)
                channel_ids.append(response.json()['items'][0]['snippet']['channelId'])
            except HTTPError as e:
                print(f"ERROR - {e}")

        return channel_ids

    def get_collaborator_urls_from_description(self):
        return re.findall('youtube.com/c/([a-zA-Z0-9_\-]+)', self.description)

    def get_collaborator_users_from_description(self):
        return re.findall('youtube.com/user/([a-zA-Z0-9_\-]+)', self.description)
