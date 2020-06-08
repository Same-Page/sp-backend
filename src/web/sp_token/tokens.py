from collections import defaultdict
from secrets import token_hex
import json

from cfg import redis_client


def get_user(token):
    user = redis_client.get(token)
    if user:
        user = json.loads(user)

    return user


def create_token(user_dict):
    token = token_hex(16)
    redis_client.set(token, json.dumps(user_dict))
    add_token_to_user(user_dict['id'], token)
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
