import json
import os

from flask import Blueprint, current_app, request, render_template

from src.controllers import get_collaborations
from src.extensions import db

graph_bp = Blueprint('graph', __name__)


@graph_bp.route('/graph')
def generate_collaboration_graph():
    target_channel_name = request.args.get('channel')
    if not target_channel_name:
        return "Target channel required in querystring", 400
    # with current_app.app_context():
    #     db.session.remove()
    #     db.engine.dispose()
    #     collabs = get_collaborations.get_collaborations_for_channel(target_channel_name)
    #
    #     nodes = {}
    #     pairs = {}
    #     edges = []
    #
    #     for collab in collabs:
    #         nodes[collab.channel_1.title] = {"fill": collab.channel_1.thumbnail_url, "id": collab.channel_1.id}
    #         nodes[collab.channel_2.title] = {"fill": collab.channel_2.thumbnail_url, "id": collab.channel_2.id}
    #         if collab in pairs:
    #             pairs[collab] = pairs[collab] + 1
    #         else:
    #             pairs[collab] = 1
    #
    #     range = sorted(pairs.values())[-1] - sorted(pairs.values())[0]
    #
    #     edge_id = 1
    #     for collab, strength in pairs.items():
    #         line_thickess = strength / range * 40 if strength / range * 40 < 25 else 25
    #         edges.append({
    #             "id": f"edge_{edge_id}",
    #             "from": collab.channel_1.title,
    #             "to": collab.channel_2.title,
    #             "channels": [collab.channel_1.id, collab.channel_2.id],
    #             "normal": {
    #                 "stroke": {
    #                     "color": "#000000",
    #                     "thickness": line_thickess,
    #                 }
    #             },
    #             "hovered": {
    #                 "stroke": {
    #                     "color": "#0d4fba",
    #                     "thickness": line_thickess,
    #                 }
    #             },
    #             "selected": {
    #                 "stroke": {
    #                     "color": "#0d4fba",
    #                     "thickness": line_thickess,
    #                 }
    #             }
    #         })
    #         edge_id += 1
    #
    # collabs_json = {
    #     "nodes": [{"id": k, "url": f"www.youtube.com/channel/{v['id']}", "fill": {"src": v["fill"]}} for k, v in nodes.items()],
    #     "edges": edges
    # }
    with open(os.path.join('data', 'violet_collabs.json'), 'r') as collab_file:
        collabs_json = json.loads(collab_file.read())

    return render_template('draw_graph.html',
                           collab_data=collabs_json,
                           node_size=1000 / len(collabs_json['nodes']))
