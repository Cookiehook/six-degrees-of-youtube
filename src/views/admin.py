from flask import Blueprint

from src.extensions import Base

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/rebuild_db')
def reset_cache():
    Base.metadata.drop_all()
    Base.metadata.create_all()
    return ''
