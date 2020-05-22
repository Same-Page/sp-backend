import os
import logging
from unittest.mock import MagicMock

import redis

logging.basicConfig(level=logging.INFO)

env = os.environ.get('sp_env', 'staging')
print(f'NOTE: running env {env}')

is_local = env.lower() == 'local'
is_local = True

API_URL = "https://api-v2.yiyechat.com"

REDIS_URL = 'redis://same-page-cache.1brzf1.0001.apse1.cache.amazonaws.com:6379'
CHAT_HISTORY_REDIS_URL = 'redis://sp-chat-history.1brzf1.0001.apse1.cache.amazonaws.com:6379'

MAX_ROOM_HISTORY = 30
# how many live connection same user can have in a room
# e.g. user open multiple tabs
MAX_USER_CONNECTION = 10


redis_client = redis.Redis.from_url(REDIS_URL)
chat_history_client = redis.Redis.from_url(CHAT_HISTORY_REDIS_URL)

if is_local:

    # REDIS_URL = CHAT_HISTORY_REDIS_URL = 'redis://0.0.0.0:6379'
    API_URL = "http://localhost:8080"

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
