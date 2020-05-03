import datetime
import re
import logging

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from models import db

logger = logging.getLogger(__name__)


class Room(db.Model):
    __tablename__ = "room"

    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer, ForeignKey("user.id"))
    name = db.Column(db.String(50))
    about = db.Column(db.String(1000))
    create_time = Column(DateTime, default=datetime.datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    background = db.Column(db.String(100))
    cover = db.Column(db.String(100))
    media = db.Column(db.String(10000))

    def __repr__(self):
        return "<Room %r>" % self.id

    def to_dict(self):

        if self.media:
            media_list = []
            try:
                for m in self.media.split():
                    media_src = re.search(r"\((.*?)\)", m).group(1)
                    media_name = re.search(r"\[(.*?)\]", m).group(1)
                    media_type = 'video/mp4'
                    if 'youtube.com' in media_src or 'youtu.be' in media_src:
                        media_type = 'video/youtube'
                    media_list.append({
                        'name': media_name,
                        'sources': [
                            {
                                'src': media_src,
                                'type': media_type
                            }
                        ]
                    })
            except:
                logger.exception(f'failed to parse media for room {self.id}')
        else:
            media_list = None

        return {
            "id": self.id,
            "owner": self.owner,
            "name": self.name,
            "about": self.about,
            "active": self.active,
            "background": self.background,
            "cover": self.cover,
            "media": media_list,
            "mediaRaw": self.media,
            "type": 'room'
        }
