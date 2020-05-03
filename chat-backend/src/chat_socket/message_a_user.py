import json
import logging

import boto3

from cfg import is_local, redis_client
# import common # cannot import common in this file!

"""
This lambda function subscribe to AWS SNS
Send message to a user in a room
A user can have multiple connections, if all connections
fail to send, remove user from the room
"""


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


def clean_dead_connections(room_id, user_id, dead_connections):
    # Remove connection/user from room data
    # Remove connection from connections map
    # TODO: enforce how many connections a user can have, similar to MAX_USER_CONNECTION
    # but not per room, it's for total
    if len(dead_connections) > 0:
        print(f'[{room_id}] found dead connections: {len(dead_connections)}')

        room = get_room(room_id)
        users = room['users']
        user_in_room = [u for u in users if u['id'] == user_id]
        if len(user_in_room) > 0:
            user = user_in_room[0]
            user['connections'] = [connection_id for connection_id in user['connections']
                                   if connection_id not in dead_connections]
            if len(user['connections']) == 0:
                room['users'] = [u for u in users if u['id'] != user_id]
                # TODO: broadcast user left
            redis_client.set(room_id, json.dumps(room))

        for connection_id in dead_connections:
            # TODO: bulk delete
            redis_client.delete(connection_id)


def lambda_handler(event, context, send_message_to_socket=None):
    data = json.loads(event['Records'][0]['Sns']['Message'])
    room_id = data['room_id']
    message = data['message']
    user = data['user']
    payload = json.dumps(message).encode('utf-8')
    endpoint_url = data['endpoint_url']
    exclude_connection = data.get('exclude_connection')

    gatewayapi = boto3.client(
        "apigatewaymanagementapi", endpoint_url=endpoint_url)

    dead_connections = []

    for connection_id in user['connections']:
        if exclude_connection == connection_id:
            continue
        try:
            if is_local:
                # Note: the local shim is not very accurate
                # exception or result won't be returned here if happened
                # in coroutine
                resp = send_message_to_socket(connection_id, payload)
            else:
                resp = gatewayapi.post_to_connection(
                    ConnectionId=connection_id, Data=payload)
        except Exception as e:
            # some connections are dropped without notice, they raise
            # exception here, we should remove these dead connections
            dead_connections.append(connection_id)
            logging.exception(
                f'Room [{room_id}] failed to send message to connection {connection_id}')

    clean_dead_connections(room_id, user['id'], dead_connections)

    return {
        'statusCode': 200,
        'body': json.dumps(f'[{room_id}] broadcast done, found dead connections: {len(dead_connections)}')
    }
