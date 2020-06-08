import os
from unittest.mock import MagicMock

import redis

REDIS_URL = os.environ.get('REDIS_URL')


if REDIS_URL:
    redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=5)
else:
    # Note that token stored in memory can only works with single
    # instance with single process. Even multiple processes in
    # a single instance won't work because token can't always be
    # found when the processes take turn to serve requests.

    # Always use a redis server unless you are developing locally.

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
