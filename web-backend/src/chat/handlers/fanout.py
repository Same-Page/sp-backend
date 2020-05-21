import json
import logging

from boto3 import client as boto3_client

from chat.cfg import is_local, redis_client
# import common # cannot import common in this file!

"""
This lambda function subscribe to AWS SNS

Broadcasting events take a long time if run synchrously since
there are many users in each room, client who send message should
get confirmation right away, so client send all users/connections SNS,
This function break it into individual users and send to another SNS topic
for parallel lambda process

This way one user having too many connections or slow connections won't
affect the other users in the room

Not breaking into each individual connection because when we find dead
connection, we can potentially delete the user from the room
"""

sns_client = boto3_client('sns')


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


def lambda_handler(event, context, queue_message=None):
    data = json.loads(event['Records'][0]['Sns']['Message'])
    room_id = data['room_id']

    room = get_room(room_id)
    users = room['users']
    for user in users:
        data['user'] = user
        queue_message(json.dumps(data))

    return {
        'statusCode': 200,
        'body': f'[{room_id}]fanout to {len(users)}'
    }
