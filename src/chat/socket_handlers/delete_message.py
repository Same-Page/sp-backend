import json
import logging

from boto3 import client as boto3_client
import requests
from cfg import redis_client

from common import get_room_messages, save_room_messages


def handle(connection, data):
    user = connection.user
    if user:
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
        if not user['isMod'] and not str(room_id) in user['rooms'] and existing_msg['user']['id'] != user['id']:
            return {
                'error': 403,
                "roomId": room_id,
                'message': 'no permission to delete message'
            }

        msgs = [m for m in msgs if m['id'] != del_msg_id]
        save_room_messages(room_id, msgs)

        payload = {
            "name": "delete message",
            "roomId": room_id,
            "data": del_msg_id,
            "connectionId": connection.id
        }
        redis_client.publish('sp', json.dumps(payload))

        return payload
    else:
        return {
            "error": 401,
            "roomId": room_id
        }
