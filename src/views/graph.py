from flask import Blueprint, current_app, request, render_template, jsonify

from src.controllers import get_collaborations
from src.extensions import db
from src.models.collaboration import Collaboration
from src.models.history import History

graph_bp = Blueprint('graph', __name__)


@graph_bp.route('/')
def generate_collaboration_graph():
    target_channel_name = request.args.get('channel')
    if not target_channel_name:  # Default for when users load the page
        target_channel_name = 'Violet Orlandi'
    with current_app.app_context():
        db.session.remove()
        db.engine.dispose()
        collabs = get_collaborations.get_collaborations_for_channel(target_channel_name)

        nodes = {}
        pairs = {}
        edges = []

        for collab in collabs:
            nodes[collab.channel_1.title] = {"fill": collab.channel_1.thumbnail_url, "id": collab.channel_1.id}
            nodes[collab.channel_2.title] = {"fill": collab.channel_2.thumbnail_url, "id": collab.channel_2.id}
            if collab in pairs:
                pairs[collab] = pairs[collab] + 1
            else:
                pairs[collab] = 1

        range = sorted(pairs.values())[-1] - sorted(pairs.values())[0]

        edge_id = 1
        for collab, strength in pairs.items():
            line_thickess = strength / range * 40 if strength / range * 40 < 25 else 25
            edges.append({
                "id": f"edge_{edge_id}",
                "from": collab.channel_1.title,
                "to": collab.channel_2.title,
                "channels": [collab.channel_1.id, collab.channel_2.id],
                "normal": {
                    "stroke": {
                        "color": "#000000",
                        "thickness": line_thickess,
                    }
                },
                "hovered": {
                    "stroke": {
                        "color": "#0d4fba",
                        "thickness": line_thickess,
                    }
                },
                "selected": {
                    "stroke": {
                        "color": "#0d4fba",
                        "thickness": line_thickess,
                    }
                }
            })
            edge_id += 1

    collabs_json = {
        "nodes": [{"id": k, "url": f"https://www.youtube.com/channel/{v['id']}", "fill": {"src": v["fill"]}} for k, v in nodes.items()],
        "edges": edges
    }
    # import json
    # import os
    # with open(os.path.join('data', 'violet_collabs.json'), 'r') as collab_file:
    #     collabs_json = json.loads(collab_file.read())

    return render_template('draw_graph.html',
                           collab_data={'nodes': sorted(collabs_json['nodes'], key=lambda x: x['id']),
                                        'edges': sorted(collabs_json['edges'], key=lambda x: x['id'])},
                           node_size=1000 / len(collabs_json['nodes']),
                           target_channel_name=target_channel_name,
                           history=History.get())


@graph_bp.route('/collaborations')
def get_collaboration_videos():
    channel_1 = request.args.get('c1')
    channel_2 = request.args.get('c2')
    if not channel_1 or not channel_2:
        return "c1 and c2 querystring must be set and by valid channel IDs", 400

    collabs = Collaboration.for_channels(channel_1, channel_2)
    return render_template("video_list.html", collabs=collabs)
