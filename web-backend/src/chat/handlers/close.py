import json
import logging

import boto3

from cfg import redis_client
from common import get_room, broadcast_user_left, delete_connection_from_rooms


# def _delete_connection_from_user(connection_id, user_id):
#     user = get_user_from_cache(user_id)
#     if user:
#         user['connections'] = [
#             c for c in user['connections'] if c != connection_id]
#         if len(user['connections']) > 0:
#             redis_client.set(user_id, json.dumps(user))
#         else:
#             redis_client.delete(user_id)


def _delete_connection_from_connections(connection_id):
    data = redis_client.get(connection_id)
    if data:
        connection = json.loads(data)
        redis_client.delete(connection_id)
        return connection


def lambda_handler(event, context):
    connection_id = event["requestContext"].get("connectionId")
    connection = _delete_connection_from_connections(connection_id)
    if connection:
        user = connection['user']
        rooms = connection['rooms']
        delete_connection_from_rooms(event, connection_id, user, rooms)
        # _delete_connection_from_user(connection_id, user['id'])


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
