import json
import logging
import time

from boto3 import client as boto3_client
import requests

# TODO: move to top level cfg? maybe
from cfg import redis_client

from common import get_user, join_room, get_connection, save_connection, get_room_messages


"""
Relationship below

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
<connection_id>: {
    'user': {'id':123, 'name':'David' ...},
    'rooms': ['google.com', 'google.com/?q=avril']
}
<room_id>: {
    'id': 'google.com',
    'users':[{'id':123, 'name':'David' ...}],
    'type': 'site',
}

"""


def handle(connection_id, data):

    room = data['room']
    token = data.get('token')
    user = get_user(token)

    if user:
        # previous_joined_room_ids = []
        # connection = get_connection(connection_id)
        # if connection:
        #     previous_joined_room_ids = connection['rooms']

        room_info = join_room(
            connection_id, user, room['id'], room['type'])
        room_info['chatHistory'] = get_room_messages(room['id'])
        room_info['roomId'] = room['id']

        # save connection - {'user':{}, 'rooms':[]}
        # need this mapping to remove user from all rooms they joined
        # save_connection(connection_id, user,
        #                 list(set(previous_joined_room_ids+[room['id']])))

        # do we need this mapping? useful when user login/logout
        # save user - {'connections':[]}
        # save_user(connection_id, user['id'])

        # TODO: client shouldn't see other user's connections
        # time.sleep(1)
        res = {
            "name": "room info",
            "data": room_info
        }

        return res

    else:
        return {
            "error": "don't support visitor yet"
        }
