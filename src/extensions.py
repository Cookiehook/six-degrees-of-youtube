from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
db.session.expire_on_commit = False
