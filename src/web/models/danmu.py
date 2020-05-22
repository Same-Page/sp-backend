from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
import datetime
from models import db


class Danmu(db.Model):
    __tablename__ = "danmu"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(db.String(50), ForeignKey("user.id"))
    video_id = Column(db.String(50))
    sec = db.Column(db.Integer)
    type = db.Column(db.String(10))

    def __repr__(self):
        return "<Danmu %r>" % self.id

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "content": self.content,
            "sec": self.sec,
            "type": self.type,
            "video_id": self.video_id,
        }
