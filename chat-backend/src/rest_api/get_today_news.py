import json
import uuid
import time

from boto3 import client as boto3_client
import boto3
import requests

from common import save_room_messages


URL = 'http://newsapi.org/v2/top-headlines?country=cn&apiKey=efd94175749d4bc19dc714fe202f7344'
ROOM_ID = 'today_news'


def get_news_and_save_to_room():
    resp = requests.get(URL)
    news = resp.json().get('articles', [])

    chat_history = []
    for n in news:
        url = n.get('url')
        if url:
            url = url.replace('http://', 'https://')
            item = {
                "id": str(uuid.uuid4()),
                "user": {
                    'id': 3,
                    'name': "news",
                    'about': "新闻推送",
                    'avatarSrc': "https://dnsofx4sf31ab.cloudfront.net/3.jpg"
                },
                "content": {
                    "type": "url",
                    "iframe_url": url,
                    "url": url,
                    "title": n.get('title')
                },
                "timestamp": int(time.time()*1000)

            }
            chat_history.append(item)
    save_room_messages(ROOM_ID, chat_history)
    return chat_history


def lambda_handler(event, context):
    return get_news_and_save_to_room()


if __name__ == "__main__":
    lambda_handler(None, None)
