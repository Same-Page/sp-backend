from flask import Blueprint, request, jsonify
from sqlalchemy.sql import func
from sqlalchemy import desc, text

from models.room import Room
from models.site_to_room import SiteToRoom
from models.user import User
from models import db
from sp_token import get_user_from_token
from sp_token.tokens import refresh_user_data

room_api = Blueprint("Room", __name__)

CREATE_ROOM_COST = 10


@room_api.route("/api/v1/rooms", methods=["GET"])
@get_user_from_token(required=False)
def get_rooms(user=None):
    room_owner_id = request.args.get('userId')
    query = db.session.query(Room, User).join(
        User).filter(Room.active == True)
    if room_owner_id:
        query = query.filter(Room.owner == room_owner_id)
    res = query.all()
    rooms = []
    for room, user in res:
        room_data = room.to_dict()
        room_data['owner'] = user.to_dict()
        rooms.append(room_data)
    return jsonify(rooms)


@room_api.route("/api/v1/room/<room_id>", methods=["GET"])
@get_user_from_token(required=False)
def get_room(room_id, user=None):
    room, user = db.session.query(Room, User).join(
        User).filter(Room.id == room_id).first()

    room_data = room.to_dict()
    room_data['owner'] = user.to_dict()
    return jsonify(room_data)


@room_api.route("/api/v1/site_to_rooms", methods=["GET"])
@get_user_from_token(required=False)
def get_site_to_rooms(user=None):
    # Only for lobby for now
    # SiteToRoom
    # res = SiteToRoom.query(...).join(Room).join(User).group_by(Room.id).all()

    res = db.session.query(SiteToRoom, Room, User).join(Room, SiteToRoom.room_id == Room.id).join(
        User, Room.owner == User.id).filter(Room.active == True).all()
    sites_to_rooms = {}

    for site_to_room, room, owner in res:
        room_data = room.to_dict()
        room_data['owner'] = owner.to_dict()
        sites_to_rooms[site_to_room.hostname] = room_data

    # Can grow to be a big payload quickly
    return jsonify(sites_to_rooms)


@room_api.route("/api/v1/create_room", methods=["POST"])
@get_user_from_token(required=True)
def create_room(user=None):

    u = User.query.filter_by(id=user['numId']).first()
    existing_room_id = request.form.get("roomId")
    if (existing_room_id):
        # todo: check if real owner of the room
        room = Room.query.filter_by(id=existing_room_id).first()
        if room.owner != u.id:
            return 403
        room.name = request.form.get("name")
        room.about = request.form.get("about")
        room.background = request.form.get("background")
        room.cover = request.form.get("cover")
        room.media = request.form.get("media")
        db.session.commit()
        res = room.to_dict()
        res['owner'] = u.to_dict()
        return jsonify(res)

    if u.credit < CREATE_ROOM_COST:
        return 'low credit', 402

    u.credit = u.credit - CREATE_ROOM_COST

    # name = request.form.get("name")
    # about = request.form.get("about")

    room = Room(owner=u.id, **request.form)
    # room = Room(name=name, about=about, owner=u.id)

    db.session.add(room)
    db.session.commit()
    if u.room:
        u.room = f'{u.room},{room.id}'
    else:
        u.room = room.id
    db.session.commit()

    token = request.headers.get("token")
    refresh_user_data(token, u)
    return jsonify(room.to_dict())
