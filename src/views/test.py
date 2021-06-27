from flask import Blueprint, jsonify

from src.controllers.entrypoint import entrypoint

test_bp = Blueprint('test', __name__)


@test_bp.route('/')
def test_method():
    entrypoint('Halocene')
    return ''
