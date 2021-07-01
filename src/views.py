from flask import Blueprint

from src.controllers import get_collaborations

view_bp = Blueprint('view', __name__)


@view_bp.route('/')
def temp():
    collabs = get_collaborations.get_collaborations_for_channel('Violet Orlandi')
    print()
    return ''