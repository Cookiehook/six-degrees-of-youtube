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

    def search(self, search_term, filter_type):
        url = self.base_url + 'search'
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'q': search_term,
            'type': filter_type,
            'maxResults': 5
        }

        response = requests.get(url, params=params)
        # TODO - Check that items is not None
        return response.json()['items']

    def find_channel_by_title(self, channel_name):
        search_results = self.search(channel_name, 'channel')
        for result in search_results:
            print(f"Channel Name: {result['snippet']['title']} - {result['id']['channelId']}")
            if result['snippet']['title'].upper() == channel_name.upper():
                return self.get_channel_for_id_name(result['id']['channelId'])

        raise RuntimeError(f"Could not find channel named '{channel_name}'")

    def find_channel_by_url(self, channel_url):
        search_results = self.search(channel_url, None)
        for result in search_results:
            if result['id']['kind'] == 'youtube#channel':
                channel = self.get_channel_for_id_name(result['id']['channelId'])
                if channel['snippet'].get('customURL', 'no url').upper() == channel_url.upper():
                    return channel

            if result['id']['kind'] == 'youtube#video':
                channel = self.get_channel_for_id_name(result['snippet']['channelId'])
                if channel['snippet'].get('customUrl', 'no url').upper() == channel_url.upper():
                    return channel

    def get_channel_for_id_name(self, channel_id=None, username=None):
        url = self.base_url + 'channels'
        params = {
            'key': self.api_key,
            'part': 'contentDetails,snippet',
        }

        if channel_id:
            params['id'] = channel_id
        else:
            params['forUsername'] = username

        response = requests.get(url, params=params)
        # TODO - Check one and only one channel is found
        return response.json()['items'][0]

    def get_channel_for_video(self, video_id):
        url = self.base_url + 'videos'
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'id': video_id,
            'maxResults': 1
        }

        response = requests.get(url, params=params)
        return self.get_channel_for_id_name(response.json()['items'][0]['snippet']['channelId'])

    def get_videos_for_playlist(self, playlist_id):
        url = self.base_url + 'playlistItems'
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': 50
        }

        response = requests.get(url, params=params)
        all_videos = response.json()['items']

        while 'nextPageToken' in response.json():
            params['pageToken'] = response.json()['nextPageToken']
            response = requests.get(url, params=params)
            all_videos.extend(response.json()['items'])

        return self.filter_video_details(all_videos)

    def get_related_channels(self, video_details):
        links = {}
        illegal_characters = ['(', ')', ',']

        for video in video_details:
            linked_channels = []
            title = video['title']
            channel_tags = []

            # Parse video titles for channel titles (eg @Halocene)
            for char in illegal_characters:
                title = title.replace(char, '')
            if "@" in title and title[0] != "@":
                channel_tags = [s.strip() for s in title.split('@')[1:]]
            elif "@" in video['title']:
                channel_tags = [s.strip() for s in title.split('@')]

            # Parse video description for channel/video mentions
            channel_ids = re.findall('youtube.com/channel/([a-zA-Z0-9_\-]+)', video['description'])
            channel_urls = re.findall('youtube.com/c/([a-zA-Z0-9_\-]+)', video['description'])
            user_ids = re.findall('youtube.com/user/([a-zA-Z0-9_\-]+)', video['description'])
            video_ids = re.findall('youtube.com/watch\?v=([a-zA-Z0-9_\-]+)', video['description'])

            linked_channels.extend(channel_ids)

            # Get channel ids from channel name
            for channel_url in channel_urls:
                linked_channels.append(self.find_channel_by_url(channel_url)['id'])
            # Get channel ids from linked users
            for user_id in user_ids:
                linked_channels.append(self.get_channel_for_id_name(username=user_id)['id'])

            # Get channel ids from linked videos
            for video_id in video_ids:
                linked_channels.append(self.get_channel_for_video(video_id)['id'])

            # Get channel ids from channel tags
            for tag in channel_tags:
                channel_id = None
                tag_words = tag.split()
                for idx, word in enumerate(tag_words):
                    try:
                        channel_id = self.find_channel_by_title(' '.join(tag_words[:idx+1]))['id']
                        print()
                    except RuntimeError:
                        pass

                if not channel_id:
                    raise RuntimeError(f'Failed to find channel from tag: {tag}')
                linked_channels.append(channel_id)

            if linked_channels:
                links[video['title']] = linked_channels

            print()
        print()
