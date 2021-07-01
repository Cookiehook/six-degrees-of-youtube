from flask import Blueprint, current_app

from src.controllers import get_collaborations
from src.extensions import db

view_bp = Blueprint('view', __name__)


@view_bp.route('/')
def temp():
    with current_app.app_context():
        db.session.remove()
        db.engine.dispose()
        collabs = get_collaborations.get_collaborations_for_channel('Halocene')
        for c in collabs:
            print(c)
    return ''
