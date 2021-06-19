import os

from flask import Flask

from stub_youtube.views.reset import reset_bp
from stub_youtube.views.channel import channel_bp
from stub_youtube.views.search import search_bp
from stub_youtube.extensions import db


def create_app():
    app = Flask(__name__)
    app.register_blueprint(channel_bp)
    app.register_blueprint(reset_bp)
    app.register_blueprint(search_bp)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres:bob@127.0.0.1:5432')
    db.init_app(app)
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    create_app().run('0.0.0.0', 5000)
