import os

from service.youtube import YoutubeApi

if __name__ == '__main__':
    api_key = os.getenv('YOUTUBE_API_KEY')
    client = YoutubeApi(api_key)
    uploads_playlist = client.find_channel_by_title('Violet Orlandi')['contentDetails']['relatedPlaylists']['uploads']
    all_videos = client.get_videos_for_playlist(uploads_playlist)
    related_channels = client.get_related_channels(all_videos)

    print()
