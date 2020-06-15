import datetime
import re
import logging
import json

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from models import db
from cfg.urls import cloud_front


logger = logging.getLogger(__name__)


class Room(db.Model):
    __tablename__ = "room"

    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer, ForeignKey("user.id"))
    name = db.Column(db.String(50))
    about = db.Column(db.String(1000))
    cover = db.Column(db.Integer, default=0)
    background = db.Column(db.Integer, default=0)
    rules = db.Column(db.String(1000))
    active = db.Column(db.Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<Room %r>" % self.id

    def to_dict(self):
        cover = None
        bg = None
        if self.cover:
            cover = f"{cloud_front}/00000_room/{self.id}-cover.jpg?v={self.cover}"
        if self.background:
            bg = f"{cloud_front}/00000_room/{self.id}-bg.jpg?v={self.background}"

        blacklist = []
        if self.rules:
            rules_dict = json.loads(self.rules)
            blacklist = rules_dict.get('blacklist', [])
        return {
            "id": self.id,
            "owner": self.owner,
            "name": self.name,
            "about": self.about,
            # "rules": self.rules,
            "blacklist": blacklist,  # should this be public to all users?
            "active": self.active,
            "background": bg,
            "cover": cover,
            "created_at": self.created_at

        }
