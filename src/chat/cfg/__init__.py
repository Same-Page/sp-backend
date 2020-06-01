import os
import logging
from unittest.mock import MagicMock

import redis

logging.basicConfig(level=logging.INFO)


MAX_ROOM_HISTORY = os.environ.get('MAX_ROOM_HISTORY', 50)
# how many live connection same user can have in a room
# e.g. user open multiple tabs
MAX_USER_CONNECTION = os.environ.get('MAX_USER_CONNECTION', 10)

# if client doesn't send heartbeat for more than this threashold
# ghost buster will delete this connection from room
HEARTBEAT_TIMOUT = os.environ.get('HEARTBEAT_TIMOUT', 60)

API_URL = os.environ.get('API_URL', "http://localhost:8080")
REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    # could use a different redis server for chat history if needed
    CHAT_HISTORY_REDIS_URL = os.environ.get(
        'CHAT_HISTORY_REDIS_URL', REDIS_URL)
    redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=3)
    chat_history_client = redis.Redis.from_url(CHAT_HISTORY_REDIS_URL)

else:
    local_cache = {}

    def get_cache(key):
        return local_cache.get(key)

    def put_cache(key, val):
        local_cache[key] = val

    def del_cache(key):
        del local_cache[key]

    redis_client = MagicMock()
    redis_client.get = get_cache
    redis_client.set = put_cache
    redis_client.delete = del_cache
    chat_history_client = redis_client
