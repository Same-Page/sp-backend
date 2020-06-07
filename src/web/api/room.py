from flask import Blueprint, request, jsonify
from sqlalchemy.sql import func
from sqlalchemy import desc, text

from models.room import Room
from models.site_to_room import SiteToRoom
from models.user import User
from models import db
from sp_token import get_user_from_token
from sp_token.tokens import refresh_user_data
from clients.s3 import upload_file

room_api = Blueprint("Room", __name__)

CREATE_ROOM_COST = 0


@room_api.route("/api/v1/rooms", methods=["GET"])
@get_user_from_token(required=False)
def get_rooms(user=None):
    room_owner_id = request.args.get('userId')
    query = db.session.query(Room, User).join(
        User).filter(Room.active == True)
    if room_owner_id:
        query = query.filter(Room.owner == room_owner_id)
    res = query.all()
    # Include same page and same site room
    rooms = [
        {
            'id': -1,
            'type': 'site',
            'name': '网站大厅',
            'about': '当前网站的所有用户都可以进入该房间。'
        },
        {
            'id': -2,
            'type': 'page',
            'name': '同网页',
            'about': '只有浏览当前网页的用户可以进入该房间。'
        }
    ]
    for room, user in res:
        room_with_owner = RoomWithOwner(room, user.to_dict())
        rooms.append(room_with_owner.to_dict())

    return jsonify(rooms)


@room_api.route("/api/v1/room/<room_id>", methods=["GET"])
@get_user_from_token(required=False)
def get_room(room_id, user=None):
    room, user = db.session.query(Room, User).join(
        User).filter(Room.id == room_id).first()

    room_with_owner = RoomWithOwner(room, user)
    return jsonify(room_with_owner.to_dict())


def get_user_room_count(user_id):
    room_count = Room.query.filter(
        Room.owner == user_id
    ).count()
    return room_count


@room_api.route("/api/v1/room", methods=["PUT"])
@get_user_from_token(required=True)
def update_room(user=None):
    room_id = request.form.get("id")

    room = Room.query.filter_by(id=room_id).first()
    if room.owner != user['id']:
        return jsonify({'error': 'not your room'}), 403

    update_room_model(room)

    db.session.commit()

    room_with_owner = RoomWithOwner(room, user)

    return jsonify(room_with_owner.to_dict())


def update_room_model(room):
    name = request.form.get("name")
    about = request.form.get("about")
    cover = request.files.get("cover")
    background = request.files.get("background")

    room.name = name
    room.about = about

    if cover:
        upload_file(cover, f"00000_room/{room.id}-cover.jpg")
        room.cover = room.cover + 1
    if background:
        upload_file(background, f"00000_room/{room.id}-bg.jpg")
        room.background = room.background + 1


@room_api.route("/api/v1/room", methods=["POST"])
@get_user_from_token(required=True)
def create_room(user=None):

    u = User.query.filter_by(id=user['id']).first()

    if u.credit < CREATE_ROOM_COST:
        return 'low credit', 402

    u.credit = u.credit - CREATE_ROOM_COST

    room = Room(owner=u.id)

    db.session.add(room)
    db.session.commit()

    update_room_model(room)
    db.session.commit()

    token = request.headers.get("token")
    refresh_user_data(token, u)

    room_with_owner = RoomWithOwner(room, user)

    return jsonify(room_with_owner.to_dict())


class RoomWithOwner:
    def __init__(self, room, user_dict):
        self.user_dict = user_dict
        self.room = room

    def to_dict(self):
        room_dict = self.room.to_dict()
        # client always expect room id to be string
        room_dict['id'] = str(room_dict['id'])
        room_dict['owner'] = self.user_dict
        return room_dict
