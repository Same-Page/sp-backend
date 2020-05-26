import functools
from flask import request, abort, jsonify

from .tokens import get_user


def get_user_from_token(required=True):
    # return user data to the decorated function
    # if required but can't find user, return 401
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token = request.headers.get("token")
            user = get_user(token) if token else None
            if not user and required:
                return jsonify({"error": "请重新登录"}), 401
            kwargs["user"] = user
            return func(*args, **kwargs)

        return wrapper

    return decorator
