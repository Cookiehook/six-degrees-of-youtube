from flask import Blueprint, jsonify

from src_new.controllers.entrypoint import entrypoint
from src_new.models.channel import Channel
from src_new.models import search
from src_new.models.video import Video

test_bp = Blueprint('test', __name__)


@test_bp.route('/')
def test_method():
    entrypoint('Violet Orlandi')
    return ''
