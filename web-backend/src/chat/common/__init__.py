import json
import logging

import requests
from boto3 import client as boto3_client

from chat.cfg import is_local, redis_client, chat_history_client, API_URL, CHAT_HISTORY_REDIS_URL, MAX_ROOM_HISTORY, MAX_USER_CONNECTION


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


def broadcast_user_left(event, room, user):

    endpoint_url = 'https://' + \
        event["requestContext"]["domainName"] + \
        '/'+event["requestContext"]["stage"]
    payload = {
        'name': 'other left',
        'data': {
            'roomId': room['id'],
            'roomType': room['type'],
            'user': user
        }
    }
    send_msg_to_room(endpoint_url, payload, room['id'])


def delete_connection_from_rooms(event, connection_id, user, rooms):
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
                        broadcast_user_left(event, room, user)


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


def broadcast_new_join(room, user):
    payload = {
        'name': 'other join',
        'data': {
            'roomId': room['id'],
            'roomType': room['type'],
            'user': user
        }
    }
    send_msg_to_room(payload, room['id'])


def save_connection(connection_id, user, room_ids):
    connection = {
        'user': user,
        'rooms': room_ids
    }
    redis_client.set(connection_id, json.dumps(connection))


def upsert_room(room):
    redis_client.set(room['id'], json.dumps(room))


def build_room_user_from_user_data(user):
    """
    Only keep fields useful
    """
    new_user = {
        'id': user['id'],
        'name': user['name'],
        'avatarSrc': user['avatarSrc'],
        'connections': []
    }
    return new_user


def join_room(connection_id, user, room_id, room_type):

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
            if connection_id in user_connections:
                # return directly if connection already in
                return room
            user_connections.append(connection_id)
            existing_user['connections'] = user_connections[-MAX_USER_CONNECTION:]
            # TODO: tell the connection client it's removed
            # so UI would show disconnected
        else:
            new_user = build_room_user_from_user_data(user)
            new_user['connections'].append(connection_id)
            # broadcast_new_join(event, room, new_user)
            # broadcast to users already in the room
            # then join the new user
            room['users'].append(new_user)

        upsert_room(room)
    else:
        new_user = build_room_user_from_user_data(user)
        new_user['connections'].append(connection_id)
        room = {
            'id': room_id,
            'type': room_type,  # why need this?
            'users': [new_user]
        }
        upsert_room(room)
    return room


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
