# Remove Lambda's pre-prepared logger handlers and use our own
# Must be done before the first logger reference, hence being above imports
import logging
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.info("Configured logger")

from flask import Flask  # noqa
from flask_sqlalchemy_session import flask_scoped_session  # noqa

from src.controllers import secrets  # noqa
from src.views.graph import graph_bp  # noqa
from src.views.admin import admin_bp  # noqa
from src.views.health import health_bp  # noqa
from src.extensions import session_factory  # noqa


def create_app():
    app = Flask(__name__)
    app.register_blueprint(graph_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)
    app.app_context().push()
    flask_scoped_session(session_factory, app)

    return app


app = create_app()
if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
