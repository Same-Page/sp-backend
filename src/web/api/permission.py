import json

from flask import Blueprint, request, jsonify

from models import db
from models.room import Room

from sp_token import get_user_from_token

permission_api = Blueprint("Permission", __name__)


@permission_api.route("/api/v1/has_permission", methods=["POST"])
@get_user_from_token(True)
def has_permission(user=None):
    """
    Insert new message and also get latest messages since offset,
    not just the message inserted
    """
    payload = request.get_json()
    action = payload["action"]
    if action == 'delete message':
        room_id = payload["room_id"]
        room = Room.query.filter(Room.id == room_id).first()
        if room:
            if room.owner == user['id']:
                return jsonify({"success": True}), 200
            else:
                return jsonify({"error": 'No permission to delete message'}),  403
        else:
            return jsonify({"error": "room not found"}), 404

    return 400
