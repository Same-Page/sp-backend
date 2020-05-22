import json
import logging

from boto3 import client as boto3_client
import requests
import redis


from cfg import REDIS_URL, API_URL
from common import get_user, get_room, get_connection, delete_connection_from_rooms, save_connection


def lambda_handler(event, context):

    connection_id = event["requestContext"].get("connectionId")
    data = json.loads(event['body'])['data']

    room = data['room']
    token = data.get('token')
    user = get_user(token)

    if user:
        previous_joined_room_ids = []
        connection = get_connection(connection_id)
        if connection:
            previous_joined_room_ids = connection['rooms']

        delete_connection_from_rooms(
            event, connection_id, user, [room['id']])
        room_ids = [r_id
                    for r_id in previous_joined_room_ids if r_id != room['id']]
        # save connection - {'user':{}, 'rooms':[]}
        save_connection(connection_id, user, room_ids)
        # save user - {'connections':[]}
        # save_user(connection_id, user['id'])

        # TODO: client shouldn't see other user's connections
        res = {
            "name": "left room",
            "data": {
                "roomId": room['id']
            }
        }

        return {
            'statusCode': 200,
            'body': json.dumps(res)
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('not logged in!')
        }


payload = {
    "action": "join",
    "data": {
        "url": 'https://zhhu.com'
    }
}
event = {
    "requestContext": {
        "domainName": "7dvmt9p591.execute-api.ap-southeast-1.amazonaws.com",
        "stage": "prod",
        "connectionId": 'a'
    },
    "body": json.dumps(payload)
}
if __name__ == "__main__":
    print(lambda_handler(event, None))
