import datetime
from unittest import TestCase
from unittest.mock import patch, call

import responses
from flask import Flask

from src import extensions
from src.models.video import Video


class VideoTest(TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        extensions.db.init_app(self.app)
        self.app.app_context().push()  # Required to allow SQLAlchemy extension to load correctly
        with self.app.app_context():
            extensions.db.create_all()
        self.published_timestamp = datetime.datetime(1970, 1, 1)
        self.default_video = Video('default_id', 'default_channel_id', 'default_title',
                                   'default_description', self.published_timestamp)

    def tearDown(self):
        with self.app.app_context():
            extensions.db.drop_all()

    @patch('src.models.video.db')
    def test_video_saved_default(self, db):
        video = Video('id', 'channel_id', 'title', 'description', self.published_timestamp)
        assert video.id == 'id'
        assert video.channel_id == 'channel_id'
        assert video.title == 'title'
        assert video.description == 'description'
        assert video.published_at == self.published_timestamp
        assert db.method_calls[0] == call.session.add(video)

    @patch('src.models.video.db')
    def test_video_not_saved(self, db):
        Video('video_id', 'channel_id', 'title', 'description', self.published_timestamp, False)
        assert db.method_calls == []

    def test_repr(self):
        assert self.default_video.__repr__() == 'default_title - default_channel_id'

    def test_known_id_from_cache(self):
        cached = Video.from_id('default_id', cache_only=True)
        assert cached == self.default_video

    def test_unknown_id_from_cache(self):
        cached = Video.from_id('unknown_id', cache_only=True)
        assert cached is None

    @patch('src.models.video.db', autospec=True)
    def test_unknown_id_from_api_success(self, db):
        api_response = [{
            "id": 'api_id',
            "snippet": {
                "channelId": "api_channel_id",
                "title": "api_title",
                "description": "api_description",
                "publishedAt": "2020-01-01T06:30:45Z"
            }
        }]

        with patch('src.models.video.Video.get') as patch_get:
            patch_get.return_value = (api_response, None)
            lookup = Video.from_id('unknown_id')
        assert lookup.id == api_response[0]['id']
        assert lookup.channel_id == api_response[0]['snippet']['channelId']
        assert lookup.title == api_response[0]['snippet']['title']
        assert lookup.description == api_response[0]['snippet']['description']
        assert lookup.published_at == datetime.datetime(2020, 1, 1, 6, 30, 45)
        assert patch_get.call_args == call('videos', params={'part': 'snippet', 'id': 'unknown_id'})
        assert db.session.add.call_args is None

    def test_unknown_id_from_api_multiple_videos(self):
        api_response = [{}, {}]
        with patch('src.models.video.Video.get') as patch_get:
            patch_get.return_value = (api_response, None)
            with self.assertRaises(AssertionError) as err:
                Video.from_id('unknown_id')
            assert err.exception.args[0] == 'Returned unexpected number of videos: [{}, {}]', err.exception.args[0]

    def test_get_collaborators_from_title(self):
        title = 'Somebody to love live @ Wembley (Cover with @Violet Orlandi, @Halocene, @Lauren Babic)'
        self.default_video.title = title
        collaborators = self.default_video.get_titles_from_title()
        assert collaborators == {'Violet Orlandi', 'Halocene', 'Lauren Babic'}

    def test_get_no_collaborators_from_title(self):
        title = 'Beat it - Micheal Jackson cover'
        self.default_video.title = title
        collaborators = self.default_video.get_titles_from_title()
        assert collaborators == set()

    def test_get_urls_from_description(self):
        description = """
        Collaborated with https://www.youtube.com/marcellroncsák
        Go see my producer's vlogs at https://www.youtube.com/joeyizzo for future updates
        Check out my second channel https://www.youtube.com/c/PlzGiveCheeseburgers"""
        self.default_video.description = description
        urls = self.default_video.get_urls_from_description()
        assert urls == {'marcellroncsák', 'joeyizzo', 'PlzGiveCheeseburgers'}

    def test_no_urls_from_description(self):
        description = """
        Halocene covers "Zombie" by  @TheCranberriesVEVO  with a few call backs to the popular
        @Bad Wolves  rendition + a few new things sprinkled in. Enjoy!
        """
        self.default_video.description = description
        urls = self.default_video.get_urls_from_description()
        assert urls == set()

    def test_get_users_from_description(self):
        description = """
        Collaborated with https://www.youtube.com/user/marcellroncsák
        Go see my producer's vlogs at https://www.youtube.com/user/joeyizzo for future updates
        Check out my second channel https://www.youtube.com/user/PlzGiveCheeseburgers"""
        self.default_video.description = description
        urls = self.default_video.get_users_from_description()
        assert urls == {'marcellroncsák', 'joeyizzo', 'PlzGiveCheeseburgers'}

    def test_no_users_from_description(self):
        description = """
        Halocene covers "Zombie" by  @TheCranberriesVEVO  with a few call backs to the popular
        @Bad Wolves  rendition + a few new things sprinkled in. Enjoy!
        """
        self.default_video.description = description
        urls = self.default_video.get_users_from_description()
        assert urls == set()

    def test_get_channel_ids_from_description(self):
        description = """
        Collaborated with https://www.youtube.com/channel/ghfpGFPIg378_-
        Go see my producer's vlogs at https://www.youtube.com/channel/ghfpGF11PIgds66 for future updates
        Check out my second channel https://www.youtube.com/channel/_-tifjePIg378"""
        self.default_video.description = description
        urls = self.default_video.get_channel_ids_from_description()
        assert urls == {'ghfpGFPIg378_-', 'ghfpGF11PIgds66', '_-tifjePIg378'}

    def test_no_channel_ids_from_description(self):
        description = """
        Halocene covers "Zombie" by  @TheCranberriesVEVO  with a few call backs to the popular
        @Bad Wolves  rendition + a few new things sprinkled in. Enjoy!
        """
        self.default_video.description = description
        urls = self.default_video.get_channel_ids_from_description()
        assert urls == set()

    def test_get_video_ids_from_description(self):
        description = """
        Collaborated with https://www.youtube.com/watch?v=ghfpGFPIg378_-
        Go see my producer's vlogs at https://www.youtu.be/ghfpGF11PIgds66 for future updates
        Check out my second channel https://www.youtube.com/watch?v=_-tifjePIg378"""
        self.default_video.description = description
        urls = self.default_video.get_video_ids_from_description()
        assert urls == {'ghfpGFPIg378_-', 'ghfpGF11PIgds66', '_-tifjePIg378'}

    def test_no_video_ids_from_description(self):
        description = """
        Halocene covers "Zombie" by  @TheCranberriesVEVO  with a few call backs to the popular
        @Bad Wolves  rendition + a few new things sprinkled in. Enjoy!
        """
        self.default_video.description = description
        urls = self.default_video.get_video_ids_from_description()
        assert urls == set()

    def test_replace_bitly_links(self):
        description = """
        Collaborated with http://bit.ly/2usJ3lq
        Go see my producer's vlogs at http://bit.ly/2usJ3lq for future updates
        Check out my second channel http://bit.ly/2usJ3lq"""
        self.default_video.description = description

        def response_callback(resp):
            resp.url = "https://youtube.com/channel/1234567890"
            return resp

        with responses.RequestsMock(response_callback=response_callback) as m:
            m.add(responses.GET, 'http://bit.ly/2usJ3lq')
            self.default_video.resolve_bitly_links()
            assert self.default_video.description.endswith(
                ' https://youtube.com/channel/1234567890  https://youtube.com/channel/1234567890  https://youtube.com/channel/1234567890 ')

    @patch('src.models.video.requests')
    def test_no_bitly_links(self, requests):
        description = """
        Halocene covers "Zombie" by  @TheCranberriesVEVO  with a few call backs to the popular
        @Bad Wolves  rendition + a few new things sprinkled in. Enjoy!
        """
        self.default_video.description = description
        self.default_video.resolve_bitly_links()
        assert requests.call_count == 0
