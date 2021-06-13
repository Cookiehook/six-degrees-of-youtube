from flask import Blueprint, jsonify, request
from jsonschema import ValidationError
from sqlalchemy.exc import IntegrityError

from stub_youtube.models.search import Search


search_bp = Blueprint('search', __name__)


@search_bp.route('/search', methods=['POST'])
def post_channel():
    try:
        search = Search(request.get_json())
    except IntegrityError as e:
        return jsonify(message='Request violated database integrity', error=e.args[0]), 400
    except ValidationError as e:
        return jsonify(message="Request payload was incorrect", error=e.args[0]), 400

    return jsonify(items=[search.json()]), 201


@search_bp.route('/search', methods=['GET'])
def get_channel():
    q = request.args.get('q')
    types = request.args.get('type').split(",")
    result = Search.query.filter_by(Search.type.in_(types), q=q)
    if not result:
        return jsonify(msg=f'No Search result with attributes {request.args}')

    return jsonify(items=[result.json()])
