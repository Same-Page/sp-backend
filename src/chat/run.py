import json
import uuid
import copy
import asyncio
import pathlib
import ssl
import websockets
import threading

from socket_handlers import join_single_room, message, leave_single_room
# from chat_socket import set_rooms, message, join_single_room, leave_single_room, close, delete_message
from connections import connections
from connection import Connection
from cfg import REDIS_URL, redis_client, chat_history_client
from redis_handlers import message_handler
# when it's single server websocket, we can keep reference to each socket
# in a dictionary in memory;
# when it's multiple servers, use redis to save each room's chat history,
# more importantly, subscribe to room message events.
# LB issue?


def handle_event(connection, data):
    action = data['action']
    data = data['data']
    res = 'no handler for ' + action

    # if action == 'join':
    #     res = set_rooms.lambda_handler(mock_event, None)['body']
    if action == 'message':
        res = message.handle(connection, data)
    if action == 'join_single':
        res = join_single_room.handle(connection, data)
    if action == 'leave_single':
        res = leave_single_room.handle(connection, data)
    # if action == 'delete_message':
    #     print('del')
    #     res = delete_message.lambda_handler(mock_event, None)['body']

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
            # close.lambda_handler(mock_event, None)
            break

start_server = websockets.serve(
    run, "localhost", 8765
)


if REDIS_URL:
    redis_message_subscriber = chat_history_client.pubsub()

    redis_message_subscriber.subscribe(**{'message': message_handler})
    thread = redis_message_subscriber.run_in_thread(sleep_time=3)

else:

    def publish_mock(channel, data):
        payload = {
            'data': data
        }
        if channel == 'message':
            thread = threading.Thread(target=message_handler, args=(payload,))
            thread.start()

    chat_history_client.publish = publish_mock


asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
