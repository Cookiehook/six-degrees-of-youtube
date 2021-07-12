from flask import Blueprint
from sqlalchemy.orm import Session

from src.extensions import engine, Base

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/rebuild_db')
def reset_cache():
    Base.metadata.drop_all()
    Base.metadata.create_all()
    return ''
