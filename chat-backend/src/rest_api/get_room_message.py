import json

from common import get_room_messages


def lambda_handler(event, context):
    room_id = event.get("queryStringParameters", {}).get('roomId')
    timestamp = event.get("queryStringParameters", {}).get('timestamp')
    res = get_room_messages(room_id)
    if timestamp:
        timestamp = int(timestamp)
        res = [m for m in res if m['timestamp'] > timestamp]
    return {
        'statusCode': 200,
        'body': json.dumps(res),
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'token'
        },
    }


if __name__ == "__main__":
    print(lambda_handler(None, None))
