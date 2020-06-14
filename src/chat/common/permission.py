import logging

import requests

from cfg import API_URL

logger = logging.getLogger(__name__)


class PermissionException(Exception):
    pass


def has_permission(action, token, room_id):
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


def check_permission(action, token, room_id=None):
    allow = has_permission(action, token, room_id)
    if not allow:
        raise PermissionException('sp permission error')
