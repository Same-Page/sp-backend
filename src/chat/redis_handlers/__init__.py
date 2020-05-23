import json
import logging
import asyncio

from common import get_room
from connections import connections

logger = logging.getLogger(__name__)


def message_handler(data):

    payload = json.loads(data['data'])
    room_id = payload['roomId']
    exclude_connection = payload['connectionId']
    room = get_room(room_id)

    users = room['users']
    for user in users:
        dead_connections = []

        for connection_id in user['connections']:
            if exclude_connection == connection_id:
                continue
            try:

                connection = connections.get(connection_id)
                if connection:
                    print(f'send_message_to_socket {connection_id}')
                    asyncio.run(connection.message(payload))

            except Exception as e:
                # some connections are dropped without notice, they raise
                # exception here, we should remove these dead connections
                dead_connections.append(connection_id)
                logger.exception(
                    f'Room [{room_id}] failed to send message to connection {connection_id}')

    print(data)
