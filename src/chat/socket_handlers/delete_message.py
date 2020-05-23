import json
import logging

from boto3 import client as boto3_client
import requests
from cfg import redis_client

from common import get_user, join_room, get_connection, save_connection, get_room_messages, save_room_messages, send_msg_to_room


def lambda_handler(event, context):
    connection_id = event["requestContext"].get("connectionId")
    data = json.loads(event['body'])['data']
    token = data.get('token')
    user = get_user(token)
    if user:
        room_id = data.get('roomId')
        del_msg_id = data.get('messageId')
        msgs = get_room_messages(room_id)
        # user can delete message if:
        # 1. user is mod
        # 2. user is room owner
        # 3. own message

        if not user['isMod']:
            if not str(room_id) in user['rooms']:

                for m in msgs:
                    if m['id'] == del_msg_id:
                        msg_sender = m['user']
                        if user['id'] != msg_sender['id']:
                            return {
                                'statusCode': 403,
                                'body': json.dumps('forbidden!')
                            }

        msgs = [m for m in msgs if m['id'] != del_msg_id]
        save_room_messages(room_id, msgs)

        payload = {
            "name": "delete message",
            "data": {
                "roomId": room_id,
                "messageId": del_msg_id
            }
        }

        endpoint_url = 'https://' + event["requestContext"]["domainName"] + \
            '/'+event["requestContext"]["stage"]

        send_msg_to_room(endpoint_url, payload, room_id,
                         exclude_connection=connection_id)

        return {
            'statusCode': 200,
            'body': json.dumps(payload)
        }
    else:
        return {
            'statusCode': 401,
            'body': json.dumps('not logged in!')
        }
