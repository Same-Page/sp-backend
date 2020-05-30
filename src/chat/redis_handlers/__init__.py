import json
import logging
import asyncio

from common import get_room
from connections import connections

logger = logging.getLogger(__name__)


def message_handler(data):

    payload = json.loads(data['data'])
    room_id = payload['roomId']
    exclude_connection_id = payload.get('connectionId')
    room = get_room(room_id)

    users = room['users']
    for user in users:
        # dead_connections = []

        for connection in user['connections']:
            connection_id = connection['id']
            if exclude_connection_id == connection_id:
                continue
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
