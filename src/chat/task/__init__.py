import json
import time
import logging

from cfg import redis_client, HEARTBEAT_TIMOUT
from common import upsert_room,  delete_connection_from_rooms

logger = logging.getLogger(__name__)


def ghost_buster():
    while True:
        try:
            kill_ghost_connections()

        except Exception as e:
            logger.exception('ghost_buster exception')
        time.sleep(20)


def kill_ghost_connections():
    # TODO: mock scan_iter() when not using redis
    # low priority, when it's single instance without redis
    # ghost connections are rare
    for key in redis_client.scan_iter("room*"):
        data = redis_client.get(key)
        if data:
            # value might already be deleted by another
            # ghost buster thread
            room = json.loads(data)

            now = time.time()
            user_ids_to_be_removed = []
            for user in room['users']:
                connection_ids_to_be_removed = []

                for connection in user['connections']:
                    time_elapse = now - connection['heartbeat']

                    if time_elapse > HEARTBEAT_TIMOUT:
                        connection_id = connection['id']
                        logger.info(
                            f'[{key}] ghost connection {connection_id} will be removed')
                        connection_ids_to_be_removed.append(connection_id)

                user['connections'] = [c for c in user['connections']
                                       if c['id'] not in connection_ids_to_be_removed]
                if (len(user['connections']) == 0):
                    user_id = user['id']
                    logger.info(f'ghost user {user_id} will be removed')
                    user_ids_to_be_removed.append(user_id)

            room['users'] = [u for u in room['users']
                             if u['id'] not in user_ids_to_be_removed]

            if len(room['users']) == 0:
                logger.info(f'ghost room {key} will be removed')
                redis_client.delete(key)
            else:
                if len(connection_ids_to_be_removed) > 0:
                    upsert_room(room)
                # TODO: broadcast user left event to other users in the room
                # low priority
