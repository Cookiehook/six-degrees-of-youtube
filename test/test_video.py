from unittest.mock import MagicMock, patch

import pytest

from src_v3.models.video import Video


def playlist_item_template(video_id='video_id', channel_id='channel_id', title='title', description='description'):
    return {
        'snippet': {
            'resourceId': {'videoId': video_id},
            'title': title,
            'channelId': channel_id,
            'description': description
        }
    }


def test_constructor():
    video = Video('video_id', 'channel_id', 'title', 'description')
    assert video.video_id == 'video_id'
    assert video.channel_id == 'channel_id'
    assert video.title == 'title'
    assert video.description == 'description'


def test_from_api_success():
    get_mock = MagicMock(return_value=([{
        'id': 'video_id',
        'snippet': {
            'title': 'title',
            'channelId': 'channel_id',
            'description': 'description'
        }
    }], None))

    with patch('src_v3.models.video.Video.get', get_mock):
        video = Video.from_api('video_id')
    assert video.video_id == 'video_id'
    assert video.channel_id == 'channel_id'
    assert video.title == 'title'
    assert video.description == 'description'


def test_from_api_multiple_returns():
    get_mock = MagicMock(return_value=([{'id': 'video_id_1'}, {'id': 'video_id_2)'}], None))

    with patch('src_v3.models.video.Video.get', get_mock):
        with pytest.raises(AssertionError) as err:
            Video.from_api('video_id')
        assert err.value.args[0] == "Returned unexpected number of videos: [{'id': 'video_id_1'}, {'id': 'video_id_2)'}]"


def test_from_playlist_one_page():
    def side_effect(url, params):
        return [playlist_item_template(video_id='id_1'), playlist_item_template(video_id='id_2'), playlist_item_template(video_id='id_3')], None

    with patch('src_v3.models.video.Video.get', MagicMock(side_effect=side_effect)):
        videos = Video.from_playlist('uploads_id')

    assert len(videos) == 3
    for idx, v in enumerate(videos):
        assert v.video_id == f"id_{idx + 1}"


def test_from_playlist_three_pages():
    def side_effect(url, params):
        if params.get('pageToken') is None:
            return [playlist_item_template(video_id='id_1'), playlist_item_template(video_id='id_2'), playlist_item_template(video_id='id_3')], 'page_2'
        if params.get('pageToken') == 'page_2':
            return [playlist_item_template(video_id='id_4'), playlist_item_template(video_id='id_5'), playlist_item_template(video_id='id_6')], 'page_3'
        if params.get('pageToken') == 'page_3':
            return [playlist_item_template(video_id='id_7'), playlist_item_template(video_id='id_8'), playlist_item_template(video_id='id_9')], None

    with patch('src_v3.models.video.Video.get', MagicMock(side_effect=side_effect)):
        videos = Video.from_playlist('uploads_id')

    assert len(videos) == 9
    for idx, v in enumerate(videos):
        assert v.video_id == f"id_{idx + 1}"


def test_get_collab_from_title_no_collaborators():
    video = Video('', '', 'There are no collaborators here', '')
    collabs = video.get_collaborators_from_title()
    assert collabs == []


def test_get_collab_from_title_two_collaborators():
    video = Video('', '', 'Video with @Halocene @Lauren Babic', '')
    collabs = video.get_collaborators_from_title()
    assert collabs == ['Halocene', 'Lauren Babic']


def test_get_collab_from_start():
    video = Video('', '', '@Halocene @Lauren Babic - Massive collaboration', '')
    collabs = video.get_collaborators_from_title()
    assert collabs == ['Halocene', 'Lauren Babic - Massive collaboration']


def test_get_collab_bad_characters():
    video = Video('', '', 'Video (ft. @Halocene @Lauren Babic) live @ Wembly', '')
    collabs = video.get_collaborators_from_title()
    assert collabs == ['Halocene', 'Lauren Babic live Wembly']


def test_get_url_from_description():
    description = """
    Starring youtube.com/c/MyGuest
    Check them out at youtube.com/MyOtherGuest for more music
    """
    video = Video('', '', '', description)
    urls = video.get_collaborator_urls_from_description()
    assert urls == ['MyGuest', 'MyOtherGuest']


def test_get_url_from_description_no_matches():
    description = "Nothing interesting to see here"
    video = Video('', '', '', description)
    urls = video.get_collaborator_urls_from_description()
    assert urls == []


def test_get_username_from_description():
    description = """
    Check out my other channel: youtube.com/user/MySecondChannel
    Starring youtube.com/user/MyGuestUser From Bobbington
    """
    video = Video('', '', '', description)
    usernames = video.get_collaborator_users_from_description()
    assert usernames == ['MySecondChannel', 'MyGuestUser']


def test_get_username_from_description_no_match():
    description = "Nothing interesting here"
    video = Video('', '', '', description)
    usernames = video.get_collaborator_users_from_description()
    assert usernames == []


def test_get_channel_id_from_description():
    description = """
    Check out my other channel: youtube.com/channel/channel_1
    Starring youtube.com/channel/channel_2 From Bobbington
    """
    video = Video('', '', '', description)
    channel_ids = video.get_collaborator_ids_from_description()
    assert channel_ids == ['channel_1', 'channel_2']


def test_get_channel_id_from_description_no_match():
    description = "Nothing to see here"
    video = Video('', '', '', description)
    channel_ids = video.get_collaborator_ids_from_description()
    assert channel_ids == []


def test_get_video_id_from_description():
    description = """
        Check out my other song: youtube.com/watch?v=fhFEJIosh349_
        Behind the scenes here youtube.com/watch?v=fdhsupHF89343-_ from the studio
        """
    video = Video('', '', '', description)
    video_ids = video.get_video_ids_from_description()
    assert video_ids == ['fhFEJIosh349_', 'fdhsupHF89343-_']


def test_get_video_id_from_description_no_match():
    description = "Nothing to see here"
    video = Video('', '', '', description)
    video_ids = video.get_video_ids_from_description()
    assert video_ids == []
