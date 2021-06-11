from flask import Blueprint

from stub_youtube.models.channel import Channel

reset_bp = Blueprint('reset', __name__)


@reset_bp.route('/reset', methods=['PATCH'])
def reset_data():
    """Deletes and rebuilds dataset from list"""
    Channel.query.delete()
    Channel(dict(id='violet_channel_id', title='Violet Orlandi', uploads='violet_uploads_id', url='violet_url', forUsername='violet_username'))
    Channel(dict(id='lauren_channel_id', title='Lauren Babic', uploads='lauren_uploads_id', url='lauren_url', forUsername='lauren_username'))
    Channel(dict(id='halocene_channel_id', title='Halocene', uploads='halocene_uploads_id', url='halocene_url', forUsername='helocene_username'))
    Channel(dict(id='f211_channel_id', title='First To Eleven', uploads='f211_uploads_id', url='f211_url', forUsername='f211_username'))
    Channel(dict(id='frogleap_channel_id', title='Frogleap Studios', uploads='frogleap_uploads_id', url='frogleap_url', forUsername='frogleap_username'))
    Channel(dict(id='hannah_channel_id', title='Hannah Boulton', uploads='hannah_uploads_id', url='hannah_url', forUsername='hannah_username'))
    Channel(dict(id='rabea_channel_id', title='Rabea', uploads='rabea_uploads_id', url='rabea_url', forUsername='rabea_username'))
    Channel(dict(id='serschen_channel_id', title='Serschen & Zaritskaya', uploads='serschen_uploads_id', url='serschen_url', forUsername='serschen_username'))
    Channel(dict(id='melodika_channel_id', title='Melodika Bros', uploads='melodika_uploads_id', url='melodika_url', forUsername='melodika_username'))

    return ''
