import logging
import statistics
import traceback
import urllib

from flask import Blueprint, current_app, request, render_template, jsonify, url_for
from flask_sqlalchemy_session import current_session

from src.controllers import get_collaborations
from src.controllers.exceptions import ChannelNotFoundException, YoutubeAuthenticationException
from src.models.channel import Channel
from src.models.collaboration import Collaboration
from src.models.history import History
from src.models.video import Video

graph_bp = Blueprint('graph', __name__)
logger = logging.getLogger()


@graph_bp.route('/')
def generate_collaboration_graph():
    logger.info("Requested endpoint '/'")
    target_channel_name = urllib.parse.unquote_plus(request.args.get('channel', ''))
    previous_channel_name = urllib.parse.unquote_plus(request.args.get('previous_channel', ''))
    if not target_channel_name:  # Default for when users load the page
        target_channel_name = 'Violet Orlandi'
    with current_app.app_context():
        collabs_json = {"nodes": [], "edges": []}
        node_size = 1
        chart_title = message = None
        history = [[urllib.parse.quote(c.channel.title), c.channel.title] for c in History.get(current_session)]

        try:
            collabs = get_collaborations.get_collaborations_for_channel(target_channel_name, previous_channel_name)
            if len(collabs) > 0:
                self_url = url_for('graph.generate_collaboration_graph', _external=True)
                collabs_json, node_size = build_anygraph_json(self_url, target_channel_name, collabs)
                chart_title = f"{target_channel_name} & {previous_channel_name}" if previous_channel_name else target_channel_name
            else:
                message = "This channel has no collaborations"
        except ChannelNotFoundException:
            message = f"Couldn't find channel named '{target_channel_name}'\n" \
                      f"Please check that the spelling and case is correct and try again."
        except YoutubeAuthenticationException as e:
            logger.error(f"Encountered authentication error: - {e}")
            message = "<p>The application has encountered an issue with the Youtube API</p>" \
                      "<p>Meanwhile, try a cached result using the popular channels button</p>"
        except Exception as e:
            logger.error(f"Failed to process collaborations for {target_channel_name} - {e}")
            traceback.print_exc()
            message = "<p>The application has encountered an issue it didn't expect</p>" \
                      "<p>Try again, or contact CookieHookHacks via twitter if the error persists</p>" \
                      "<p>Meanwhile, try a cached result using the popular channels button</p>"

    return render_template('draw_graph.html',
                           collab_data={'nodes': sorted(collabs_json['nodes'], key=lambda x: x['id']),
                                        'edges': sorted(collabs_json['edges'], key=lambda x: x['id'])},
                           node_size=node_size,
                           chart_title=chart_title,
                           history=history,
                           message=message)


@graph_bp.route("/calc/uploads", methods=['POST'])
def get_uploads_for_channel():
    channel_id = request.get_json()['channel']
    videos = get_collaborations.get_uploads_for_channel(channel_id)
    return jsonify(videos=videos)


@graph_bp.route("/calc/parse_videos", methods=['POST'])
def get_collaborators_for_videos():
    video_ids = request.get_json()['videos']
    guest_channels = set()
    for video_id in video_ids:
        video = Video.from_id(video_id)
        logger.debug(f"Parsing host video '{video}'")
        guest_channels.update(get_collaborations.get_channels_from_description(video))
        guest_channels.update(get_collaborations.get_channels_from_title(video))
    return jsonify(channels=[c.id for c in guest_channels])


@graph_bp.route("/calc/process_collaborations", methods=['POST'])
def process_collaborations():
    target_channel = request.get_json()['target_channel']
    video_ids = request.get_json()['videos']
    get_collaborations.populate_collaborations(target_channel, video_ids)
    return ''


@graph_bp.route('/dual_collaborations')
def get_dual_collaboration_videos():
    logger.info("Requested endpoint '/collaborations'")
    channel_1 = Channel.from_id(request.args.get('c1'))
    channel_2 = Channel.from_id(request.args.get('c2'))
    # The set filters duplicates that appear when there are 2+ channels collaborating on 1 video
    videos = {c.video for c in Collaboration.for_channels(channel_1, channel_2)}
    return render_template("dual_videos_list.html", channel_1=channel_1, channel_2=channel_2,
                           videos=sorted(videos, key=lambda v: v.published_at, reverse=True))


@graph_bp.route('/single_collaborations')
def get_single_collaboration_videos():
    logger.info("Requested endpoint '/collaborations'")
    channel = Channel.from_id(request.args.get('c'))
    # The set filters duplicates that appear when there are 2+ channels collaborating on 1 video
    videos = {c.video for c in Collaboration.for_single_channel(channel)}
    return render_template("single_videos_list.html", channel=channel,
                           videos=sorted(videos, key=lambda v: v.published_at, reverse=True))


def build_anygraph_json(self_url, previous_channel, collabs):
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

    # Remove the most aggressive deviations, so we don't end up with whisker thin lines for single collabs
    index = -1
    std_dev = statistics.stdev(sorted(pairs.values()))
    range = sorted(pairs.values())[-1] - sorted(pairs.values())[0]
    while std_dev > 50:
        index -= 1
        std_dev = statistics.stdev(sorted(pairs.values())[:index])
        range = sorted(pairs.values())[index] - sorted(pairs.values())[0]

    # Node size maximum is 100. Edge width maximum is node size. Otherwise clipping occurs
    node_size = 1000 / len(nodes) if 1000 / len(nodes) < 100 else 100
    edge_id = 1
    for collab, strength in pairs.items():
        line_thickess = strength / range * 40 if strength / range * 40 < node_size else node_size
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
        "nodes": [{"id": k,
                   "channel_id": v["id"],
                   "url": f"{self_url}?channel={urllib.parse.quote(k)}&previous_channel={urllib.parse.quote(previous_channel)}",
                   "fill": {"src": v["fill"]}} for k, v in nodes.items()],
        "edges": edges
    }
    # import json
    # import os
    # with open(os.path.join('data', 'violet_collabs.json'), 'r') as collab_file:
    #     collabs_json = json.loads(collab_file.read())
    return collabs_json, node_size
