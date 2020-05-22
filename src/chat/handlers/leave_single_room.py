import json
import logging

from boto3 import client as boto3_client
import requests
import redis


from cfg import REDIS_URL, API_URL
from common import get_user, get_room, get_connection, delete_connection_from_rooms, save_connection


def handle(connection, data):
    """
    Remove connection from room
    Remove room from connection
    """
    connection_id = connection.id

    room_id = data['roomId']
    token = data.get('token')
    # user = get_user(token) # user is already on connection object
    user = connection.user
    if user:

        delete_connection_from_rooms(connection_id, user, [room_id])

        connection.leave_room(room_id)
        return {
            "name": "left room",
            "data": {
                "roomId": room_id
            }
        }

    else:
        return {
            'error': 'not logged in'

        }
