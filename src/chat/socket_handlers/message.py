import json
import logging
import uuid
import datetime

import copy
import asyncio

import boto3
from boto3 import client as boto3_client

from common import get_user, get_room, get_room_messages, save_room_messages
from cfg import redis_client

logger = logging.getLogger(__name__)


def save_msg(data, room_id):
    data = copy.deepcopy(data)
    """
    Input
        chat_message = {
            "id": message_id,
            "user": sender,
            "content": content
        }
    add created?
    """
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

    if declared_type == 'file':
        return 'file'
    # Youtube urls are handled above already
    # check for urls
    if content.lower().startswith('http'):
        return 'url'

    return declared_type


def get_url_message(content):
    # Use bilibili iframe player
    # if 'bilibili.com/video/av' in content.lower():
    #     aid = content.split('av')[1].split('/')[0].split('?')[0]
    #     return {
    #         'type': 'url',
    #         'value': content,
    #         'iframe_url': f'https://player.bilibili.com/player.html?aid={aid}&high_quality=1&danmaku=0',
    #         'title': content
    #     }
    # normal url
    return {
        'type': 'url',
        'value': content,
        'name': content
    }


def get_content(payload):
    """
    Not relying on client entirely, when client send type = text/file,
    it could turn out to be media (image, sound, video);
    # TODO: unit test this function thoroughly!
    """

    declared_type = payload['type']

    if declared_type == 'text':
        content = payload['value']
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
                "value": payload['url'],
                "name": payload['fileName']
            }
        else:
            return {
                "type": analyzed_content_type,
                "value": payload['url'],
            }
    elif declared_type == 'url':
        # TODO: this should be call page share or something
        # page title is required from client for this case
        url = payload['url']
        iframe_url = url
        if 'bilibili.com/video/av' in url.lower():
            aid = url.split('av')[1].split('/')[0].split('?')[0]
            iframe_url = f'https://player.bilibili.com/player.html?aid={aid}&high_quality=1&danmaku=0'

        return {
            "type": declared_type,
            "value": url,
            "iframe_url": iframe_url,
            "name": payload['title'],
        }


def handle(connection, data):
    """
    Client tell room id,
    broadcast to that room
    """
    user = connection.user
    message_id = data['id']
    room_id = data['roomId']
    room = get_room(room_id)

    if room:
        # Check user is in room or not, might be kicked or blacklisted
        user_ids_in_room = [u['id'] for u in room['users']]
        if user['id'] not in user_ids_in_room:
            return {
                'error': 'user_not_in_room',
                'roomId': room_id
            }

         # TODO: sanitize input!!!!!!
        content = get_content(data['content'])

        sender = get_sender_basic_info(user)

        # sometimes sender's connection isn't in the room
        # add it to room first? Better to fix the source of bug then patching here..

        chat_message = {
            "id": message_id,
            # "roomId": room_id,
            "user": sender,
            "content": content,
            'created_at': datetime.datetime.utcnow().isoformat()

        }
        payload = {
            "name": "chat_message",
            "roomId": room_id,
            "data": chat_message,
            "connectionId": connection.id
        }

        logger.info(f"[{room_id}] {sender['name']}: {content['value']}")

        # exclude sender's connectionId id so they don't receive twice
        redis_client.publish('sp', json.dumps(payload))

        save_msg(chat_message, room_id)
        return payload

    return {
        'error': 'no room'
    }
