import json
import logging
import asyncio

import requests
from boto3 import client as boto3_client

from cfg import redis_client, chat_history_client, API_URL,\
    MAX_ROOM_HISTORY, MAX_USER_CONNECTION

from connections import connections

logger = logging.getLogger(__name__)


def get_connection(connection_id):
    data = redis_client.get(connection_id)
    if data:
        connection = json.loads(data)
        return connection
    return None


def get_room(room_id):
    if not room_id:
        return None
    data = redis_client.get(room_id)
    if data:
        room = json.loads(data)
        # ensure basic fields
        room['users'] = room.get('users', [])
        return room
    return None


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


# def get_user_from_cache(user_id):
#     data = redis_client.get(user_id)
#     if data:
#         user = json.loads(data)
#         return user
#     return None


def get_user(token):
    if not token:
        return None
    headers = {
        "token": token
    }
    resp = requests.get(f"{API_URL}/api/v1/user", headers=headers)
    if resp.ok:
        return resp.json()
    return None


def broadcast_user_left(room_id, user):

    payload = {
        'name': 'other left',
        'data': {
            'roomId': room_id,
            'user': user
        }
    }
    send_msg_to_room(payload, room_id)


def send_msg_to_room(payload, room_id, exclude_connection=[]):
    # Shouldn't need this, when room message is updated, it should
    # trigger event automatically

    room = get_room(room_id)
    users = room['users']
    for user in users:
        dead_connections = []

        for connection_id in user['connections']:
            if exclude_connection == connection_id:
                continue
            try:
                # Note: the local shim is not very accurate
                # exception or result won't be returned here if happened
                # in coroutine
                send_message_to_socket(connection_id, payload)
            except Exception as e:
                # some connections are dropped without notice, they raise
                # exception here, we should remove these dead connections
                dead_connections.append(connection_id)
                logger.exception(
                    f'Room [{room_id}] failed to send message to connection {connection_id}')

        # clean_dead_connections(room_id, user['id'], dead_connections)


def send_message_to_socket(connection_id, data):

    connection = connections.get(connection_id)
    if connection:
        print(f'send_message_to_socket {connection_id}')
        connection.message(data)
    else:
        pass
        # logging.warn(f'connection not exist {connection_id}')


def delete_connection_from_rooms(connection_id, user, rooms):
    user_has_left = False
    for room_id in rooms:
        room = get_room(room_id)
        if room:
            user_in_room = [u for u in room['users'] if u['id'] == user['id']]
            if len(user_in_room) > 0:
                user_in_room = user_in_room[0]
                if connection_id in user_in_room['connections']:
                    # remove connection from user
                    user_in_room['connections'].remove(connection_id)
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

                    redis_client.set(room_id, json.dumps(room))
                    if user_has_left:
                        # broadcast user left
                        broadcast_user_left(room_id, user)


# def send_msg_to_room(payload, room_id, exclude_connection=None):
#     """
#     Sending message to clients is slow, send to SNS for fanout
#     first, then process in parallel

#     exclude_connection is usually the sender, sender's own message
#     is returned as soon as server receives it, shouldn't send again to sender
#     """
#     data = {
#         'message': payload,
#         'room_id': room_id,
#         'exclude_connection': exclude_connection
#     }
#     queue_broadcast(json.dumps(data))


def save_connection(connection_id, user, room_ids):
    connection = {
        'user': user,
        'rooms': room_ids
    }
    redis_client.set(connection_id, json.dumps(connection))


# def save_user(connection_id, user_id):
    # TODO: better naming, this is saving connection to user
    # user_connection_data = get_user_from_cache(user_id)
    # if user_connection_data:
    #     user_connection_data['connections'].append(connection_id)
    #     user_connection_data['connections'] = list(
    #         set(user_connection_data['connections']))
    # else:
    #     user_connection_data = {
    #         'connections': [connection_id]
    #     }
    # redis_client.set(user_id, json.dumps(user_connection_data))
