import logging
import os

from flask import Flask

from src.extensions import db
from src.views.graph import graph_bp

logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)
    app.register_blueprint(graph_bp)
    app.app_context().push()

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres:bob@127.0.0.1:5432')
    db.init_app(app)
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
