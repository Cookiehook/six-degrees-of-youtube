from flask import Blueprint, current_app, request, render_template

from src.controllers import get_collaborations
from src.extensions import db

graph_bp = Blueprint('graph', __name__)


@graph_bp.route('/graph')
def generate_collaboration_graph():
    target_channel_name = request.args.get('channel')
    if not target_channel_name:
        return "Target channel required in querystring", 400
    with current_app.app_context():
        db.session.remove()
        db.engine.dispose()
        collabs = get_collaborations.get_collaborations_for_channel(target_channel_name)

        nodes = {}
        pairs = {}
        edges = []

        for collab in collabs:
            nodes[collab.channel_1.title] = collab.channel_1.thumbnail_url
            nodes[collab.channel_2.title] = collab.channel_2.thumbnail_url
            if collab in pairs:
                pairs[collab] = pairs[collab] + 1
            else:
                pairs[collab] = 1

        range = sorted(pairs.values())[-1] - sorted(pairs.values())[0]

        for collab, strength in pairs.items():
            line_thickess = strength / range * 40 if strength / range * 40 < 25 else 10
            edges.append({
                "from": collab.channel_1.title,
                "to": collab.channel_2.title,
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

    collabs_json = {
        "nodes": [{"id": k, "fill": {"src": v}} for k, v in nodes.items()],
        "edges": edges
    }
    return render_template('draw_graph.html',
                           collab_data=collabs_json,
                           node_size=1000 / len(nodes))
