import json
import logging

from boto3 import client as boto3_client
import requests
from cfg import redis_client

from common import get_room_messages, save_room_messages
from common.permission import check_permission

ACTION_NAME = "delete_message"


def handle(connection, data):
    user = connection.user
    room_id = data.get('roomId')
    del_msg_id = data.get('messageId')
    msgs = get_room_messages(room_id)
    # user can delete message if:
    # 1. user is mod
    # 2. user is room owner
    # 3. own message

    existing_msg = [m for m in msgs if m['id'] == del_msg_id]
    if len(existing_msg) > 0:
        existing_msg = existing_msg[0]
    else:
        return {
            'error': 404,
            "roomId": room_id,
            'message': 'message not found'
        }

    if not existing_msg['user']['id'] == user['id']:
        check_permission(ACTION_NAME, connection.token, room_id)

    msgs = [m for m in msgs if m['id'] != del_msg_id]
    save_room_messages(room_id, msgs)

    payload = {
        "name": ACTION_NAME,
        "roomId": room_id,
        "data": del_msg_id,
        "connectionId": connection.id
    }
    redis_client.publish('sp', json.dumps(payload))
    return payload
