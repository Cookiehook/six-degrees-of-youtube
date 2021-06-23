import os

from flask import Flask

from src_new.extensions import db
from src_new.views.test import test_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(test_bp)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres:bob@127.0.0.1:5432')
    db.init_app(app)
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    create_app().run('0.0.0.0', 5000)
