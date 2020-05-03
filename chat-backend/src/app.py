import json
import uuid
import copy

import asyncio
import pathlib
import ssl
import websockets

from chat_socket import set_rooms, message, join_single_room, leave_single_room, close, delete_message
from chat_socket.local_sockets import local_sockets
from cfg import CHAT_SOCKET_DOMAIN


def handle_event(mock_event, action):
    res = f'no handler for action {action}'
    if action == 'join':
        res = set_rooms.lambda_handler(mock_event, None)['body']
    if action == 'message':
        res = message.lambda_handler(mock_event, None)['body']
    if action == 'join_single':
        res = join_single_room.lambda_handler(mock_event, None)['body']
    if action == 'leave_single':
        res = leave_single_room.lambda_handler(mock_event, None)['body']
    if action == 'delete_message':
        print('del')
        res = delete_message.lambda_handler(mock_event, None)['body']

    return res


async def hello(websocket, path):
    connection_id = str(uuid.uuid4())
    print(f'{connection_id} connected')
    local_sockets[connection_id] = websocket
    mock_event = {
        'requestContext': {
            'connectionId': connection_id,
            'domainName': CHAT_SOCKET_DOMAIN,
            'stage': 'prod'
        },
        'body': ''
    }
    while True:
        try:
            data_str = await websocket.recv()
            data = json.loads(data_str)
            action = data['action']
            print(f'{connection_id} {action}')
            # mock how event is passed to aws lambda functions
            mock_event['body'] = data_str
            res = handle_event(mock_event, action)

            await websocket.send(res)

        except websockets.ConnectionClosed:
            print(f"{connection_id} closed by client")
            del local_sockets[connection_id]
            close.lambda_handler(mock_event, None)
            break


ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
localhost_pem = pathlib.Path(__file__).with_name(
    "local_cert.pem")
localhost_key_pem = pathlib.Path(__file__).with_name("key.pem")
ssl_context.load_cert_chain(localhost_pem, keyfile=localhost_key_pem)

start_server = websockets.serve(
    hello, "localhost", 8765,
    ssl=ssl_context
)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
