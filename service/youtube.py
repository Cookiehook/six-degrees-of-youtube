import requests


class YoutubeApi:

    def __init__(self, api_key):
        self.base_url = 'https://www.googleapis.com/youtube/v3/'
        self.api_key = api_key

    def filter_video_details(self, raw_videos):
        filtered_videos = []
        for video in raw_videos:
            filtered_videos.append({
                'title': video['snippet']['title'],
                'description': video['snippet']['description'],
                'video_id': video['snippet']['resourceId']['videoId'],
            })
        return filtered_videos

    def get_upload_playlist_for_channel(self, name):
        url = self.base_url + 'channels'
        params = {
            'key': self.api_key,
            'part': 'contentDetails',
            'forUsername': name
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

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
        related_videos = {}

        for video in video_details:
            if "@" in video['title']:
                print(video['title'])
                print(video['title'].split("@"))
