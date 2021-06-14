def video_template(kind='youtube#playlistItem', video_id='1', channel_id='1', title='title', description='desc'):
    return {
        'kind': kind,
        'snippet': {
            'resourceId': {'videoId': video_id},
            'channelId': channel_id,
            'title': title,
            'description': description
        }
    }
