import json

from boto3 import client as boto3_client
import boto3
from boto3.dynamodb.conditions import Attr

from common import chat_history_client


def lambda_handler(event, context):
    news_id = event.get("queryStringParameters", {}).get('id')
    news = chat_history_client.get(news_id)
    data = ''
    if news:
        status_code = 200
        data = news.decode()
    else:
        status_code = 404

    return {
        'statusCode': status_code,
        'body': data,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'token'
        },
    }


if __name__ == "__main__":
    event = {
        "queryStringParameters": {
            "id": "f2516272-025b-4929-af7c-78e621cf38b0"
        }
    }
    print(lambda_handler(event, None))
