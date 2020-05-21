import json
import logging

import redis

from common import get_room, get_room_messages, get_connection
from cfg import redis_client


def lambda_handler(event, context):

    connection_id = event["requestContext"].get("connectionId")
    data = json.loads(event['body'])['data']

    # This is only called by chatbox not injection script
    # And chatbox always getChatHistory
    get_chat_history = data.get('getChatHistory')
    rooms = data.get('rooms', [])
    res = {}
    if len(rooms) == 0:
        # If client doesn't specify which room
        # return room info of all rooms this connection is in
        connection = get_connection(connection_id)
        if connection:
            rooms = connection['rooms']

    for room_id in rooms:

        room = get_room(room_id) or {}
        if get_chat_history:
            room['chatHistory'] = get_room_messages(room_id)
            if room.get('users'):
                # client shouldn't see other user's connections
                for u in room["users"]:
                    del u['connections']
        res[room_id] = room

    payload = {
        "name": "room info",
        "data": res,
        "query": data
    }
    return {
        'statusCode': 200,
        'body': json.dumps(payload)
    }
