from flask import Blueprint, jsonify, request
from jsonschema import ValidationError
from sqlalchemy.exc import IntegrityError

from stub_youtube.models.channel import Channel


channel_bp = Blueprint('channel', __name__)


@channel_bp.route('/channels', methods=['POST'])
def post_channel():
    try:
        channel = Channel(request.get_json())
    except IntegrityError as e:
        return jsonify(message='Request violated database integrity', error=e.args[0]), 400
    except ValidationError as e:
        return jsonify(message="Request payload was incorrect", error=e.args[0]), 400

    return jsonify(items=[channel.json()]), 201


@channel_bp.route('/channels', methods=['GET'])
def get_channel():
    if request.args.get('id'):
        channel = Channel.query.filter_by(id=request.args.get('id')).first()
    else:
        channel = Channel.query.filter_by(forUsername=request.args.get('forUsername')).first()

    if not channel:
        return jsonify(msg=f'No Channel with attributes {request.args}')

    return jsonify(items=[channel.json()])
