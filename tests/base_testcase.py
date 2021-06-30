from unittest import TestCase

from flask import Flask

from src import extensions


class YoutubeTestCase(TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        extensions.db.init_app(self.app)
        self.app.app_context().push()  # Required to allow SQLAlchemy extension to load correctly
        with self.app.app_context():
            extensions.db.create_all()

    def tearDown(self):
        with self.app.app_context():
            extensions.db.drop_all()
