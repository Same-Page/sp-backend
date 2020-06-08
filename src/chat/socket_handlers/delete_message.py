import json
import logging

from boto3 import client as boto3_client
import requests
from cfg import redis_client

from common import get_room_messages, save_room_messages
from common.permission import has_permission

ACTION_NAME = "delete message"


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

        if user['isMod'] or existing_msg['user']['id'] == user['id'] or \
                has_permission(ACTION_NAME, room_id, connection.token):

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

        else:
            return {
                'error': 403,
                "roomId": room_id,
                'message': 'no permission to delete message'
            }

    else:
        return {
            "error": 401,
            "roomId": room_id
        }
