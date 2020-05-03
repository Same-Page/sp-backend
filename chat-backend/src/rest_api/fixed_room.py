import json

from boto3 import client as boto3_client
from boto3.dynamodb.conditions import Attr
import requests

from common import get_room
from cfg import API_URL


def lambda_handler(event, context):
    user_id = event.get("queryStringParameters", {}).get('userId')
    params = {}
    if user_id:
        params['userId'] = user_id

    resp = requests.get(f"{API_URL}/api/v1/rooms", params=params)
    if resp.ok:

        rooms = resp.json()

        for room in rooms:
            realtime_room_data = get_room(room['id'])
            if realtime_room_data:
                room['userCount'] = len(realtime_room_data['users'])
            else:
                room['userCount'] = 0

        return {
            'statusCode': 200,
            'body': json.dumps(rooms),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'token'
            },
        }


if __name__ == "__main__":
    print(lambda_handler(None, None))
