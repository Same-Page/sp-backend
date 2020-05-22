import json
import time
import asyncio

from .message_a_user import lambda_handler as message_a_user
from .fanout import lambda_handler as fanout
from .local_sockets import local_sockets


def queue_broadcast(message):
    # simulate delay on server
    time.sleep(0.1)
    mock_event = {
        'Records': [{
            'Sns': {
                'Message': message
            }
        }]
    }
    fanout(mock_event, None, queue_message)


def queue_message(message):
    # simulate delay on server
    time.sleep(0.1)
    mock_event = {
        'Records': [{
            'Sns': {
                'Message': message
            }
        }]
    }
    message_a_user(mock_event, None,
                   send_message_to_socket=send_message_to_socket)


def send_message_to_socket(connection_id, data):
    print(f'send_message_to_socket {connection_id}')
    socket = local_sockets[connection_id]
    asyncio.create_task(socket.send(data.decode()))
