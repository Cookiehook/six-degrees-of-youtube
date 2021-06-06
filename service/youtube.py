import json
import re

import requests


class YoutubeApi:

    def __init__(self, api_key):
        self.base_url = 'https://www.googleapis.com/youtube/v3/'
        self.api_key = api_key
        self.parsed_channels = []

    def filter_video_details(self, raw_videos):
        filtered_videos = []
        for video in raw_videos:
            filtered_videos.append({
                'title': video['snippet']['title'],
                'description': video['snippet']['description'],
                'video_id': video['snippet']['resourceId']['videoId'],
            })
        return filtered_videos

    def get_uploads_for_channel(self, name):
        url = self.base_url + 'search'
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'q': name,
            'type': 'channel',
            'maxResults': 50
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        for result in response.json()['items']:
            channel_id = result['id']['channelId']
            channel = self.get_channel_by_id(channel_id)
            print(f"Channel Name: {channel['snippet']['title']} - {result['id']['channelId']}")
            if channel['snippet']['title'].upper() == name.upper():
                self.parsed_channels.append(channel_id)
                return channel['contentDetails']['relatedPlaylists']['uploads']
        raise RuntimeError(f"Could not find channel named '{name}'")

    def get_channel_by_id(self, channel_id):
        url = self.base_url + 'channels'
        params = {
            'key': self.api_key,
            'part': 'contentDetails,snippet',
            'id': channel_id
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()['items'][0]

    def get_videos_for_playlist(self, playlist_id):
        url = self.base_url + 'playlistItems'
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': 50
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        all_videos = response.json()['items']

        while 'nextPageToken' in response.json():
            params['pageToken'] = response.json()['nextPageToken']
            response = requests.get(url, params=params)
            response.raise_for_status()
            all_videos.extend(response.json()['items'])

        return self.filter_video_details(all_videos)

    def get_related_channels(self, video_details):
        related_channels = {}
        illegal_characters = ['(', ')', ',']

        for video in video_details:
            title = video['title']
            channel_tags = None

            # Parse video titles for tagged channels
            for char in illegal_characters:
                title = title.replace(char, '')
            if "@" in title and title[0] != "@":
                channel_tags = [s.strip() for s in title.split('@')[1:]]
            elif "@" in video['title']:
                channel_tags = [s.strip() for s in title.split('@')]

            # Parse video description for channel/video mentions
            channel_ids = re.findall('www.youtube.com/(?:channel|c)/([a-zA-Z0-9_\-]+)', video['description'])
            user_ids = re.findall('www.youtube.com/(?:user)/([a-zA-Z0-9_\-]+)', video['description'])

            if user_ids:
                print()

            related_channels[video['video_id']] = channel_tags

        print(json.dumps(related_channels, indent=2))
