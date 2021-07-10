from flask import Blueprint

from src.extensions import db

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('resetcache')
def reset_cache():
    db.drop_all()
    db.create_all()
    return ''
