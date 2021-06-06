import os

from service.youtube import YoutubeApi

if __name__ == '__main__':
    api_key = os.getenv('YOUTUBE_API_KEY')
    client = YoutubeApi(api_key)
    playlist_id = client.get_upload_playlist_for_channel('Halocene')
    all_videos = client.get_videos_for_playlist(playlist_id)
    related_channels = client.get_related_channels(all_videos)

    print()
