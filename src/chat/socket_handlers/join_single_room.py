import json
import logging
import time

from boto3 import client as boto3_client
import requests

from cfg import redis_client, MAX_USER_CONNECTION

from common import get_user, get_room, get_room_messages
from redis_handlers import message_handler

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


def upsert_room(room):
    redis_client.set(room['id'], json.dumps(room))


def build_room_user_from_user_data(user, connection_id):
    """
    Only keep fields useful
    """
    new_user = {
        'id': user['id'],
        'name': user['name'],
        'avatarSrc': user['avatarSrc'],
        'connections': [connection_id]
    }
    return new_user


def broadcast_new_join(connection_id, room_id, user):
    payload = {
        'name': 'other join',
        "roomId": room_id,
        "connectionId": connection_id,
        'user':  user

    }
    redis_client.publish('sp-user', json.dumps(payload))


def join_room(connection, user, room_id):

    # check if room already exists
    # check if connection already joined this room
    room = get_room(room_id)

    if room:

        existing_users_in_room = room['users']
        existing_user = [
            u for u in existing_users_in_room if u['id'] == user['id']]
        if len(existing_user) > 0:
            existing_user = existing_user[0]
        else:
            existing_user = None

        if existing_user:
            user_connections = existing_user['connections']
            if connection.id in user_connections:
                # return directly if connection already in
                return room
            user_connections.append(connection.id)
            existing_user['connections'] = user_connections[-MAX_USER_CONNECTION:]
            # TODO: tell the connection client it's removed
            # so UI would show disconnected
        else:
            new_user = build_room_user_from_user_data(user, connection.id)

            broadcast_new_join(connection.id, room_id, new_user)
            # broadcast to users already in the room
            # then join the new user
            room['users'].append(new_user)

        upsert_room(room)
    else:
        new_user = build_room_user_from_user_data(user, connection.id)
        room = {
            'id': room_id,
            'users': [new_user]
        }
        upsert_room(room)
    return room


def handle(connection, data):

    room = data['room']
    token = data.get('token')
    user = get_user(token)
    room_id = room['id']
    if user:
        connection.user = user
        room_info = join_room(connection, user, room_id)
        connection.join_room(room_id)

        room_info['chatHistory'] = get_room_messages(room_id)

        res = {
            "name": "room info",
            "roomId": room_id,
            "data": room_info
        }

        return res
    else:
        return {
            "error": 401,
            "roomId": room_id
        }
