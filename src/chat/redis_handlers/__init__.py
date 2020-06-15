import json
import logging
import asyncio

from common import get_room
from connections import connections

logger = logging.getLogger(__name__)


def send_msg_to_connection(connection_id, payload, room_id=None):
    connection = connections.get(connection_id)
    if connection:
        # logger.debug(f'{connection_id} is in this server')

        try:
            asyncio.run(connection.message(payload))

        except Exception as e:
            # some connections are dropped without notice, they raise
            # exception here, we should remove these dead connections?
            # dead_connections.append(connection_id)
            logger.exception(
                f'Room [{room_id}] failed to send message to connection {connection_id}')
    else:

        # logger.debug(f'{connection_id} is NOT in this server')
        pass


def message_handler(data):
    try:
        payload = json.loads(data['data'])
        room_id = payload.get('roomId')
        exclude_connection_id = payload.get('connectionId')
        connection_ids = payload.get('connectionIds')
        # Either send to all users in a room or send to specific user
        # if connectionIds is in payload, send to specific connections
        # rather than whole room
        if connection_ids:
            for connection_id in connection_ids:
                send_msg_to_connection(connection_id, payload, room_id)
        else:
            room = get_room(room_id)
            users = room['users']
            for user in users:
                # dead_connections = []
                for connection in user['connections']:
                    connection_id = connection['id']
                    if exclude_connection_id == connection_id:
                        continue
                    send_msg_to_connection(connection_id, payload, room_id)
    except Exception as e:
        logger.exception('exception in redis subscriber')
