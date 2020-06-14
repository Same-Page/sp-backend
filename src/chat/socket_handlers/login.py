import json
import logging
import time

import boto3

from cfg import redis_client
from common import get_user


def handle(connection, data):
    """
    store token and user object to connection
    if token is valid
    """
    token = data['token']
    user = get_user(token)
    if user:
        login_success = True
        connection.token = token
        connection.user = user
    else:
        login_success = False

    res = {
        "name": "login",
        "success": login_success
    }

    return res
