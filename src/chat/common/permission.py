import logging

import requests

from cfg import API_URL

logger = logging.getLogger(__name__)


def has_permission(action, room_id, token):
    headers = {
        "token": token
    }
    payload = {
        "action": action,
        "room_id": room_id
    }
    try:
        resp = requests.post(f"{API_URL}/api/v1/has_permission",
                             headers=headers, json=payload)
    except Exception as e:
        logger.exception(e)
        return False
    return resp.ok
