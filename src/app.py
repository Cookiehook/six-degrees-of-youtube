import logging

# Remove Lambda's pre-prepared logger handlers and use our own
# Must be done before the first logger reference, hence being above imports
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.info("Configured logger")

from flask import Flask  # noqa

from src.controllers import secrets  # noqa
from src.views.graph import graph_bp  # noqa
from src.views.admin import admin_bp  # noqa


def create_app():
    app = Flask(__name__)
    app.register_blueprint(graph_bp)
    app.register_blueprint(admin_bp)
    app.app_context().push()

    return app


app = create_app()
if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
