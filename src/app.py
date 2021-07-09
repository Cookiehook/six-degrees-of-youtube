import logging

# Remove Lambda's pre-prepared logger handlers and use our own
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.info("Configured logger")

import aws_lambda_wsgi
from flask import Flask

from src.controllers import secrets
from src.extensions import db
from src.views.graph import graph_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(graph_bp)
    app.app_context().push()

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = secrets.get_secret("six-degrees-of-youtube-db-dsn")
    logger.info("Initialising DB")
    db.init_app(app)
    logger.info("Creating DB tables")
    with app.app_context():
        db.create_all()
    logger.info("Finished creating tables")

    return app


def entrypoint(event, context):
    return aws_lambda_wsgi.response(create_app(), event, context)


if __name__ == '__main__':
    create_app().run('0.0.0.0', 5000)
