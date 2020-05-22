import json
import logging

from boto3 import client as boto3_client
import requests

from common import get_room_messages, get_user, get_room, get_connection, delete_connection_from_rooms, send_msg_to_room, join_room, save_connection, delete_connection_from_rooms
from cfg import redis_client

"""

1 user    ---    multiple devices
1 device  ---    multiple browers
1 browser ---    multiple tabs

1 tab     ---    1 socket
1 socket  ---    multiple rooms

1 user    ---    multiple sockets multiple rooms

Data in cache

<user_id>: {
    'connections': ['sdcxzv', '2j3klf']
}
^^ this one seems never useful?

<connection_id>: {
    'user': {'id':123, 'name':'David' ...},
    'rooms': ['google.com', 'google.com/?q=avril']
}

Most important one below
<room_id>: {
    'id': 'google.com',
    'users':[{'id':123, 'name':'David' ...}],
    'type': 'site',
}

"""


def lambda_handler(event, context):

    connection_id = event["requestContext"].get("connectionId")
    data = json.loads(event['body'])['data']

    rooms = data['rooms']
    room_ids = [r['id'] for r in rooms]
    token = data.get('token')
    get_chat_history = data.get('getChatHistory')

    user = get_user(token)

    if user:
        previous_joined_room_ids = []
        connection = get_connection(connection_id)
        if connection:
            previous_joined_room_ids = connection['rooms']

        # join room if not already in
        joined_rooms = {}
        for room in rooms:
            room_info = join_room(
                connection_id, user, room['id'], room['type'], event)
            if get_chat_history:
                room_info['chatHistory'] = get_room_messages(room['id'])
            joined_rooms[room['id']] = room_info

        # leave room not in payload
        for room_id in previous_joined_room_ids:
            if not (room_id in room_ids):
                delete_connection_from_rooms(
                    event, connection_id, user, [room_id])

        # save connection - {'user':{}, 'rooms':[]}
        save_connection(connection_id, user, room_ids)
        # save user - {'connections':[]}
        # save_user(connection_id, user['id'])

        # TODO: client shouldn't see other user's connections
        res = {
            "name": "room info",
            "data": joined_rooms
        }

        return {
            'statusCode': 200,
            'body': json.dumps(res)
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('not logged in!')
        }


payload = {
    "action": "join",
    "data": {
        "url": 'https://zhhu.com'
    }
}
event = {
    "requestContext": {
        "domainName": "7dvmt9p591.execute-api.ap-southeast-1.amazonaws.com",
        "stage": "prod",
        "connectionId": 'a'
    },
    "body": json.dumps(payload)
}
if __name__ == "__main__":
    print(lambda_handler(event, None))
