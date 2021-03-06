import json
import logging
import asyncio

import requests
from boto3 import client as boto3_client

from cfg import redis_client, chat_history_client, API_URL,\
    MAX_ROOM_HISTORY, MAX_USER_CONNECTION

from connections import connections

logger = logging.getLogger(__name__)


def get_room(room_id):
    if not room_id:
        return None
    data = redis_client.get(f'room-{room_id}')
    if data:
        room = json.loads(data)
        # ensure basic fields
        room['users'] = room.get('users', [])
        return room
    return None


def upsert_room(room):
    room_id = room['id']
    redis_client.set(f'room-{room_id}', json.dumps(room))


def get_room_messages(room_id):
    if not room_id:
        return []
    data = chat_history_client.get(f'chat-history-{room_id}')
    if data:
        chat_hisotry = json.loads(data)
        return chat_hisotry
    return []


def save_room_messages(room_id, chat_history):
    chat_history = chat_history[-MAX_ROOM_HISTORY:]
    chat_history_client.set(
        f'chat-history-{room_id}', json.dumps(chat_history))


def get_user(token):
    # TBD: it's faster to call redis cache directly
    # not sure if there will be any logic we want to
    # keep in the get endpoint; also maybe api and
    # socket won't share the same cache
    if not token:
        return None
    headers = {
        "token": token
    }
    resp = requests.get(f"{API_URL}/api/v1/user", headers=headers)

    if resp.ok:
        return resp.json()
    return None


def broadcast_user_left(connection_id, room_id, user):
    payload = {
        'name': 'other_left',
        "roomId": room_id,
        "connectionId": connection_id,
        'user':  user

    }
    redis_client.publish('sp', json.dumps(payload))


def delete_connection_from_rooms(connection, room_ids):
    user = connection.user
    connection_id = connection.id
    if user:
        user_has_left = False
        for room_id in room_ids:
            room = get_room(room_id)
            if room:
                user_in_room = [u for u in room['users']
                                if u['id'] == user['id']]
                if len(user_in_room) > 0:
                    user_in_room = user_in_room[0]
                    connection_in_room = [
                        c for c in user_in_room['connections'] if c['id'] == connection_id]
                    if len(connection_in_room) > 0:
                        connection_in_room = connection_in_room[0]
                        # remove connection from user
                        user_in_room['connections'] = [
                            c for c in user_in_room['connections'] if c['id'] != connection_id]

                        if len(user_in_room['connections']) == 0:
                            # remove user from room
                            room['users'] = [u for u in room['users']
                                             if u['id'] != user['id']]
                            if len(room['users']) == 0:
                                # delete room
                                # fix rooms are also deleted, should be fine
                                # since chat history stays
                                redis_client.delete(room_id)
                                return
                            else:
                                user_has_left = True

                        upsert_room(room)
                        if user_has_left:
                            # broadcast user left
                            broadcast_user_left(connection_id, room_id, user)
