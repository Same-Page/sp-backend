import json
import logging
import time

from boto3 import client as boto3_client
import requests

from cfg import redis_client, MAX_USER_CONNECTION

from common import get_user, get_room, get_room_messages, upsert_room
from redis_handlers import message_handler
from common.permission import has_permission

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
ACTION_NAME = "join_room"


def build_room_connection(connection_id):
    return {
        'id': connection_id,
        'created_at': time.time(),
        'heartbeat': time.time()
    }


def build_room_user_from_user_data(user, connection_id):
    """
    Only keep fields useful
    """
    new_user = {
        'id': user['id'],
        'name': user['name'],
        'avatarSrc': user['avatarSrc'],
        'connections': [build_room_connection(connection_id)]
    }
    return new_user


def broadcast_new_join(connection_id, room_id, user):
    payload = {
        'name': 'other_join',
        "roomId": room_id,
        "connectionId": connection_id,
        'user':  user

    }
    redis_client.publish('sp', json.dumps(payload))


def join_room(connection, user, room_id):

    # check if room already exists
    # check if connection already joined this room
    # TODO: check if user is allowed to join this room
    # need to check room data from db

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
            existing_connection = [
                c for c in user_connections if c['id'] == connection.id]
            if len(existing_connection) > 0:
                # return directly if connection already in
                # TODO: should tell client about this
                return room
            user_connections.append(build_room_connection(connection.id))
            existing_user['connections'] = user_connections[-MAX_USER_CONNECTION:]
            # TODO: tell the connection client it's removed due to max connection limit
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

    token = data.get('token')
    room_id = data['roomId']
    user = get_user(token)

    if user:
        connection.user = user
        connection.token = token

        if has_permission(ACTION_NAME, room_id, token):

            room_info = join_room(connection, user, room_id)
            connection.join_room(room_id)
            room_info['chatHistory'] = get_room_messages(room_id)
            res = {
                "name": "room_info",
                "roomId": room_id,
                "data": room_info
            }
            return res
        else:
            return {
                "name": "forbidden_to_join",
                "roomId": room_id
            }
    else:

        return {
            "error": 401,
            "roomId": room_id
        }
