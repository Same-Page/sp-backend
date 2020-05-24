import json
import logging

import boto3

from cfg import redis_client
from common import delete_connection_from_rooms


def handle(connection):
    delete_connection_from_rooms(connection, connection.room_ids)
