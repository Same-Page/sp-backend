from sqlalchemy import Column, Integer, String, DateTime
import datetime

from models import db


class Message(db.Model):
    __tablename__ = "message"

    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.Integer)
    receiver = db.Column(db.Integer)
    message = db.Column(db.String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<Message %r>" % self.id

    def to_dict(self):
        return {
            "id": self.id,
            "from": self.sender,
            "to": self.receiver,
            "content": self.message,
            "created_at": self.created_at,
        }
