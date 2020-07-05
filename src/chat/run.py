import json
import uuid
import copy
import asyncio
import pathlib
import ssl
import websockets
import threading
import logging

from socket_handlers import join_single_room, message, leave_single_room,\
    close, heartbeat, delete_message, login, kick_user

from connections import connections
from connection import Connection
from cfg import REDIS_URL, redis_client, SSL
from redis_handlers import message_handler
from task import ghost_buster
from common.permission import PermissionException

# when it's single server websocket, we can keep reference to each socket
# in a dictionary in memory or use redis server;
# when it's multiple servers, have to use redis to save each room's chat history,
# more importantly, subscribe to room message events.

logger = logging.getLogger(__name__)


def handle_event(connection, data):
    action = data['action']
    data = data['data']

    room_id = data.get('roomId')
    res = {
        "error": 'no_handler',
        "name": action,
        "roomId": room_id
    }
    try:
        if action == 'login':
            res = login.handle(connection, data)
        if action == 'heartbeat':
            res = heartbeat.handle(connection, data)
        if action == 'join_room':
            res = join_single_room.handle(connection, data)
        if action == 'leave_room':
            res = leave_single_room.handle(connection, data)
        if action == 'message':
            res = message.handle(connection, data)
        if action == 'delete_message':
            res = delete_message.handle(connection, data)
        if action == 'kick_user':
            res = kick_user.handle(connection, data)

    except PermissionException:
        logger.error('permission error')
        res["error"] = 'forbidden'
    except Exception:
        logger.exception('exception not handled')
        res["error"] = 'server_error'

    res = json.dumps(res)
    return res


async def run(websocket, path):
    connection = Connection(websocket)
    while True:
        try:
            data_str = await websocket.recv()
            data = json.loads(data_str)
            res = handle_event(connection, data)
            await websocket.send(res)

        except websockets.ConnectionClosed:
            print(f"{connection.id} closed by client")
            connection.close()
            close.handle(connection)
            break

if SSL:
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    localhost_pem = pathlib.Path(__file__).with_name(
        "local_cert.pem")
    localhost_key_pem = pathlib.Path(__file__).with_name("key.pem")
    ssl_context.load_cert_chain(localhost_pem, keyfile=localhost_key_pem)

    start_server = websockets.serve(
        run, "0.0.0.0", 8765,
        ssl=ssl_context
    )
else:
    start_server = websockets.serve(
        run, "0.0.0.0", 8765
    )


redis_thread = None


def subscribe_to_redis_event():
    # TODO: try sqs for better stability
    global redis_thread
    if redis_thread and redis_thread.is_alive():
        # logger.debug('redis listener is healthy')
        pass
    else:
        try:
            logger.info('register redis listener')
            redis_message_subscriber = redis_client.pubsub()
            redis_message_subscriber.subscribe(**{'sp': message_handler})
            redis_thread = redis_message_subscriber.run_in_thread(sleep_time=3)
        except:
            logger.exception('register redis listener failed')

    threading.Timer(10, subscribe_to_redis_event).start()


if REDIS_URL:
    subscribe_to_redis_event()
else:

    def publish_mock(channel, data):
        payload = {
            'data': data
        }
        thread = threading.Thread(target=message_handler, args=(payload,))
        thread.start()

    redis_client.publish = publish_mock


# keep killing ghost connections every couple minutes
ghost_buster_thread = threading.Thread(target=ghost_buster)
ghost_buster_thread.start()


loop = asyncio.get_event_loop()
# the webscoekt server
loop.run_until_complete(start_server)
loop.run_forever()
