import json
import logging
import uuid
import time

import copy

import boto3
from boto3 import client as boto3_client

from common import get_user, get_room, get_room_messages, save_room_messages, send_msg_to_room


def save_msg(data, room_id):
    data = copy.deepcopy(data)
    """
    Input
        chat_message = {
            "id": message_id,
            "roomId": room_id,
            "roomType": room_type,
            "user": sender,
            "content": content
        }
    Remove roomId and roomType, add timestamp
    """
    del data['roomId']
    del data['roomType']
    data['timestamp'] = int(time.time()*1000)
    chat_history = get_room_messages(room_id)
    chat_history.append(data)
    save_room_messages(room_id, chat_history)


def get_sender_basic_info(user):
    # only return basic info
    return {
        'id': user['id'],
        'name': user['name'],
        'avatarSrc': user['avatarSrc']
    }


def check_content_type(content, declared_type):
    image_types = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if any(image_type in content.lower() for image_type in image_types):
        return 'image'
    video_types = ['.mp4', '.webm', '.ogg', '.flv', '.mov']
    audio_types = ['.mp3', '.wav']
    youtube_keywords = ['youtube.com', 'youtu.be']
    media_types = video_types+audio_types+youtube_keywords
    if any(media_type in content.lower() for media_type in media_types):
        return 'media'

    # Youtube urls are handled above already
    # check for urls
    if content.lower().startswith('http'):
        return 'url'

    return declared_type


def get_url_message(content):
    # Use bilibili iframe player
    if 'bilibili.com/video/av' in content.lower():
        aid = content.split('av')[1].split('/')[0].split('?')[0]
        return {
            'type': 'url',
            'url': content,
            'iframe_url': f'https://player.bilibili.com/player.html?aid={aid}&high_quality=1&danmaku=0',
            'title': content
        }
    # normal url
    return {
        'type': 'url',
        'url': content,
        'title': content
    }


def get_content(payload):
    """
    Not relying on client entirely, when client send type = text/file,
    it could turn out to be media (image, sound, video);
    """

    declared_type = payload['type']

    if declared_type == 'text':
        content = payload['text']
        # TODO: sanitize input
        analyzed_content_type = check_content_type(content, declared_type)
        if analyzed_content_type == 'url':
            return get_url_message(content)
        return {
            "type": analyzed_content_type,
            "value": content
        }

    elif declared_type == 'file':
        analyzed_content_type = check_content_type(
            payload['url'], declared_type)
        if analyzed_content_type == 'file':
            return {
                "type": analyzed_content_type,
                "url": payload['url'],
                "fileName": payload['fileName']
            }
        else:
            return {
                "type": analyzed_content_type,
                "value": payload['url'],
            }
    elif declared_type == 'url':
        url = payload['url']
        iframe_url = url
        if 'bilibili.com/video/av' in url.lower():
            aid = url.split('av')[1].split('/')[0].split('?')[0]
            iframe_url = f'https://player.bilibili.com/player.html?aid={aid}&high_quality=1&danmaku=0'

        return {
            "type": declared_type,
            "url": url,
            "iframe_url": iframe_url,
            "title": payload['title'],
        }


def lambda_handler(event, context):
    """
    Client tell room id,
    broadcast to the room
    """
    connection_id = event["requestContext"].get("connectionId")
    data = json.loads(event['body'])['data']
    message_id = data['id']
    room_id = data['roomId']
    content = get_content(data['content'])
    # TODO: sanitize input!!!!!!

    room = get_room(room_id)
    # get sender from token
    sender = get_sender_basic_info(get_user(data.get('token')))
    if sender and room:

        # sometimes sender's connection isn't in the room
        # add it to room first? Better to fix the source of bug then patching here..

        room_type = room['type']
        chat_message = {
            "id": message_id,
            "roomId": room_id,
            "roomType": room_type,
            "user": sender,
            "content": content
        }
        payload = {
            "name": "chat message",
            "data": chat_message
        }
        endpoint_url = 'https://' + \
            event["requestContext"]["domainName"] + \
            '/'+event["requestContext"]["stage"]
        send_msg_to_room(endpoint_url, payload, room_id,
                         exclude_connection=connection_id)
        save_msg(chat_message, room_id)

        return {
            'statusCode': 200,
            'body': json.dumps(payload)
        }
    return {
        'statusCode': 400,
        'body': json.dumps('room not exist!')
    }
