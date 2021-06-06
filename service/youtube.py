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

    def search_for_channel(self, search_term, match_term='title', filter_type='channel'):
        url = self.base_url + 'search'
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'q': search_term,
            'type': filter_type,
            'maxResults': 5
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        for result in response.json()['items']:
            if result['id']['kind'] == 'youtube#channel':
                channel_id = result['id']['channelId']
                channel = self.get_channel(channel_id)
                print(f"Channel Name: {channel['snippet'][match_term]} - {result['id']['channelId']}")
                if channel['snippet'][match_term].upper() == search_term.upper():
                    return channel
            if result['id']['kind'] == 'youtube#video':
                channel = self.get_channel(channel_id=result['snippet']['channelId'])
                if channel['snippet'].get('customUrl') == search_term:
                    return channel

        raise RuntimeError(f"Could not find channel named '{search_term}'")

    def get_channel(self, channel_id=None, username=None):
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
        response.raise_for_status()
        return response.json()['items'][0]

    def get_videos_for_playlist(self, playlist_id):
        url = self.base_url + 'playlistItems'
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': 5
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

    def get_video_owner(self, video_id):
        url = self.base_url + 'videos'
        params = {
            'key': self.api_key,
            'part': 'snippet,contentDetails',
            'id': video_id,
        }

        response = requests.get(url, params=params)
        # response.raise_for_status()
        print()

    def get_related_channels(self, video_details):
        links = {}
        illegal_characters = ['(', ')', ',']

        for video in video_details:
            linked_channels = []
            title = video['title']
            channel_tags = []

            # Parse video titles for tagged channels
            for char in illegal_characters:
                title = title.replace(char, '')
            if "@" in title and title[0] != "@":
                channel_tags = [s.strip() for s in title.split('@')[1:]]
            elif "@" in video['title']:
                channel_tags = [s.strip() for s in title.split('@')]

            # Parse video description for channel/video mentions
            channel_ids = re.findall('www.youtube.com/channel/([a-zA-Z0-9_\-]+)', video['description'])
            channel_urls = re.findall('www.youtube.com/c/([a-zA-Z0-9_\-]+)', video['description'])
            user_ids = re.findall('www.youtube.com/user/([a-zA-Z0-9_\-]+)', video['description'])
            video_ids = re.findall('www.youtube.com/watch\?v=([a-zA-Z0-9_\-]+)', video['description'])

            linked_channels.extend(channel_ids)

            # Get channel ids from channel name
            for channel_url in channel_urls:
                linked_channels.append(self.search_for_channel(channel_url, match_term='customURL', filter_type=None)['id'])

            # Get channel ids from linked users
            for user_id in user_ids:
                linked_channels.append(self.get_channel(username=user_id)['id'])

            # Get channel ids from linked videos
            for video_id in video_ids:
                linked_channels.append(self.get_video_owner(video_id))

            # Get channel ids from channel tags
            for tag in channel_tags:
                channel_id = None
                tag_words = tag.split()
                for idx, word in enumerate(tag_words):
                    try:
                        channel_id = self.search_for_channel(' '.join(tag_words[:idx+1]))['id']
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