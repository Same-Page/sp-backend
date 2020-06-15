import json
import logging
import time

import boto3

from cfg import redis_client
from common import get_room, upsert_room
from common.permission import check_permission

ACTION_NAME = "kick_user"


def handle(connection, data):
    """
    Check permission
    Check if target user is in room
    Remove target user
    Retrun if kick is successful
    Broadcast user is gone/kicked
    """

    room_id = data['roomId']
    userId = data['userId']
    check_permission(ACTION_NAME, connection.token, room_id)

    room = get_room(room_id)

    res = {
        "name": ACTION_NAME,
        "roomId": room_id,
    }

    if room:
        users_in_room = room['users']
        user_in_room = [u for u in room['users']
                        if u['id'] == userId]
        if len(user_in_room) > 0:
            users_in_room[:] = [u for u in room['users']
                                if u['id'] != userId]
            upsert_room(room)
            target_user = user_in_room[0]
            # broadcast user kicked
            user_kicked_msg_payload = {
                'name': 'user_kicked',
                "roomId": room_id,
                'user':  target_user

            }
            redis_client.publish('sp', json.dumps(user_kicked_msg_payload))

            # tell user himself he's kicked
            self_kicked_msg_payload = {
                "name": "self_kicked",
                "roomId": room_id,
                "connectionIds": [c['id'] for c in target_user['connections']]
            }
            redis_client.publish('sp', json.dumps(self_kicked_msg_payload))

            res['success']: True
        else:
            res['error'] = 'user_not_in_room'
    else:
        res['error'] = 'room_not_exist'

    return res
