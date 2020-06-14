from flask import Blueprint, request, jsonify
from sqlalchemy.sql import func
from sqlalchemy import desc, text
import json

from models.room import Room
from models.user import User
from models.site_to_room import SiteToRoom
from models.user import User
from models import db
from sp_token import get_user_from_token
from sp_token.tokens import refresh_user_data
from clients.s3 import upload_file
from cfg import redis_client

room_api = Blueprint("Room", __name__)

CREATE_ROOM_COST = 0

# the GET endpoints are also using POST method because room id
# is sometimes url


def get_same_page_room(url):
    return {
        'id': url,
        'color': '#52c41a',
        'type': 'page',
        'name': '同网页',
        'cover': 'https://i7.pngflow.com/pngimage/676/782/png-night-sky-star-background-material-blue-night-sky-star-blue-poster-banner-clipart.png',
        'about': '只有浏览当前网页的用户可以进入该房间。'
    }


def get_same_site_room(domain):
    return {
        'id': domain,
        'type': 'site',
        'name': '网站大厅',
        'color': '#40a9ff',
        'cover': 'https://dnsofx4sf31ab.cloudfront.net/00000_chat_upload/30-party.jpeg',
        'about': '当前网站的所有用户都可以进入该房间。'
    }


@room_api.route("/api/v1/get_rooms", methods=["POST"])
@get_user_from_token(required=False)
def get_rooms(user=None):

    payload = request.get_json()

    room_owner_id = payload.get('userId')
    url = payload.get('url')
    domain = payload.get('domain')

    query = db.session.query(Room, User).join(
        User).filter(Room.active == True)
    rooms = []
    if room_owner_id:
        query = query.filter(Room.owner == room_owner_id)
    else:
        # Include same page and same site room
        rooms = [
            RoomWithOwner(get_same_page_room(url)).to_dict(),
            RoomWithOwner(get_same_site_room(domain)).to_dict()
        ]
    res = query.all()

    user_created_rooms = []
    for room, user in res:
        room_with_owner = RoomWithOwner(room.to_dict(), user.to_dict())
        user_created_rooms.append(room_with_owner.to_dict())

    user_created_rooms = sorted(
        user_created_rooms, key=lambda r: r['userCount'], reverse=True)
    rooms.extend(user_created_rooms)
    return jsonify(rooms)


@room_api.route("/api/v1/room", methods=["POST"])
@get_user_from_token(required=False)
def get_room(user=None):
    payload = request.get_json()

    room_id = payload['roomId']
    room_type = payload.get('roomType')

    if room_type == 'page':
        return jsonify(RoomWithOwner(get_same_page_room(room_id)).to_dict())
    if room_type == 'site':
        return jsonify(RoomWithOwner(get_same_site_room(room_id)).to_dict())

    room, user = db.session.query(Room, User).join(
        User).filter(Room.id == room_id).first()

    room_with_owner = RoomWithOwner(room.to_dict(), user)
    return jsonify(room_with_owner.to_dict())


def get_user_room_count(user_id):
    room_count = Room.query.filter(
        Room.owner == user_id
    ).count()
    return room_count


@room_api.route("/api/v1/room/<room_id>/blacklist", methods=["GET"])
@get_user_from_token(required=True)
def get_blacklist_user(room_id, user=None):
    room = Room.query.filter_by(id=room_id).first()
    res = []
    if room.rules:
        rules = json.loads(room.rules)
        blacklist = rules.get('blacklist', [])
        users = User.query.filter(User.id.in_(blacklist)).all()
        res = [u.to_dict() for u in users]

    return jsonify(res)


@room_api.route("/api/v1/room/blacklist", methods=["POST"])
@get_user_from_token(required=True)
def blacklist_user(user=None):
    payload = request.get_json()
    room_id = payload["roomId"]
    target_user_id = payload["userId"]
    room = Room.query.filter_by(id=room_id).first()
    if not (user['isMod'] or room.owner == user['id']):
        return jsonify({'error': 'not your room'}), 403

    if room.rules:
        rules = json.loads(room.rules)
    else:
        rules = {
            'blacklist': []
        }

    rules['blacklist'].append(target_user_id)

    room.rules = json.dumps(rules)

    db.session.commit()

    return '', 200


@room_api.route("/api/v1/room", methods=["PUT"])
@get_user_from_token(required=True)
def update_room(user=None):
    room_id = request.form.get("id")

    room = Room.query.filter_by(id=room_id).first()
    if not (user['isMod'] or room.owner == user['id']):
        return jsonify({'error': 'not your room'}), 403

    update_room_model(room)

    db.session.commit()

    room_with_owner = RoomWithOwner(room.to_dict(), user)

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

    room_with_owner = RoomWithOwner(room.to_dict(), user)

    return jsonify(room_with_owner.to_dict())


class RoomWithOwner:
    def __init__(self, room_dict, user_dict=None):
        self.user_dict = user_dict
        self.room_dict = room_dict
        self.user_count = 0

        room_in_cache = redis_client.get(f'room-{room_dict["id"]}')
        if room_in_cache:
            room_in_cache = json.loads(room_in_cache)
            self.user_count = len(room_in_cache.get('users', []))

    def to_dict(self):
        # maybe deep copy first
        room_dict = self.room_dict
        # client always expect room id to be string
        room_dict['id'] = str(room_dict['id'])
        room_dict['owner'] = self.user_dict
        room_dict['userCount'] = self.user_count
        return room_dict
