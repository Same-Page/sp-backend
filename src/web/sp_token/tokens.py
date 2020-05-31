from collections import defaultdict
from secrets import token_hex
import redis
import json
from unittest.mock import MagicMock

from cfg import REDIS_URL

# TODO: redis client is general cache, not just for token
# move to a dedicated file
if REDIS_URL:
    redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=3)
else:
    # Note that token stored in memory can only works with single
    # instance with single process. Even multiple processes in
    # a single instance won't work because token can't always be
    # found when the processes take turn to serve requests.

    # Always use a redis server unless developing locally.

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


def get_user(token):
    user = redis_client.get(token)
    if user:
        user = json.loads(user)

    return user


def create_token(user):
    token = token_hex(16)
    redis_client.set(token, json.dumps(user.to_dict()))
    add_token_to_user(user.id, token)
    return token


def refresh_user_data(token, user):
    redis_client.set(token, json.dumps(user.to_dict()))


def add_token_to_user(user_id, token):
    # one user can have multiple tokens, so value is list
    key = f'user-id-{user_id}'
    tokens = redis_client.get(key)
    if tokens:
        tokens = json.loads(tokens)
    else:
        tokens = []
    tokens.append(token)
    redis_client.set(key, json.dumps(tokens))


def remove_token_from_user(user_id, token):
    key = f'user-id-{user_id}'
    tokens = redis_client.get(key)
    if tokens:
        tokens = json.loads(tokens)
        tokens = [t for t in tokens if t != token]
        redis_client.set(key, json.dumps(tokens))

    else:
        # TODO: log error
        pass


def revoke_all_tokens_of_user(user_id):

    key = f'user-id-{user_id}'
    tokens = redis_client.get(key)
    if tokens:
        tokens = json.loads(tokens)
        for token in tokens:
            revoke_token(token)


def revoke_token(token):
    """
    Only revoke one given token, not all tokens of user
    """
    user = get_user(token)
    if not user:
        return False

    redis_client.delete(token)
    remove_token_from_user(user['id'], token)
    return True
