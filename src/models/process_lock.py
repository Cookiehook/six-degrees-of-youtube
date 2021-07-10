from src.extensions import db


class ProcessLock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_name = db.Column(db.String)

    def __init__(self, channel_name):
        self.channel_name = channel_name

        db.session.add(self)
        db.session.commit()

    @classmethod
    def get(cls, channel_name):
        return cls.query.filter_by(channel_name=channel_name).all()

    def remove(self):
        db.session.delete(self)
        db.session.commit()
