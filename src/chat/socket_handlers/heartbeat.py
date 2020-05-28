import json
import logging
import time

import boto3

from cfg import redis_client
from common import get_room, upsert_room


def handle(connection, data):
    """
    Heartbeat is used to let server know this connection is alive
    and still connected to the room

    Meanwhile, it tells client that the connection is fine, if server
    doesn't see this connection in the room, it could try to add it.
    But that complicates the logic, tell client connection is not found
    in the room and let client handle it.
    """

    room_id = data['roomId']
    room = get_room(room_id)
    user = connection.user
    # user object is already attached to the connection object
    # when joining the room

    res = {
        "name": "heartbeat",
        "success": False,
        "roomId": room_id
    }
    if room:
        user_in_room = [u for u in room['users']
                        if u['id'] == user['id']]
        if len(user_in_room) > 0:
            user_in_room = user_in_room[0]
            connection_in_room = [
                c for c in user_in_room['connections'] if c['id'] == connection.id]

            if len(connection_in_room) > 0:
                connection_in_room = connection_in_room[0]
                connection_in_room['heartbeat'] = time.time()
                res['success'] = True
                upsert_room(room)
            else:
                res['error'] = 'user is in room but connection not found'
        else:
            res['error'] = 'user is not in room'
    else:
        res['error'] = 'room not exist!'

    return res
