from flask import Blueprint, request, jsonify
from sqlalchemy import func

from models import db
from models.user import User
from models.follow import Follow
from sp_token import get_user_from_token


follow_api = Blueprint("Follow", __name__)


@follow_api.route("/api/v1/followers", methods=["GET"])
@get_user_from_token(required=True)
def get_followers(user=None):
    """
    Get followers of user, require auth
    """
    offset = request.args.get("offset", 0)
    followers = (
        db.session.query(User)
        .join(Follow, Follow.follower_id == User.id)
        .filter(Follow.user_id == user['id'], Follow.active == True)
        .offset(offset)
        .limit(20)
    )
    followers = [user.to_dict() for user in followers]
    return jsonify(followers)


@follow_api.route("/api/v1/followings", methods=["GET"])
@get_user_from_token(required=True)
def get_followings(user=None):
    """
    Get followings of user, require auth
    """
    offset = request.args.get("offset", 0)
    followers = (
        db.session.query(User)
        .join(Follow, Follow.user_id == User.id)
        .filter(Follow.follower_id == user['id'], Follow.active == True)
        .offset(offset)
        .limit(20)
    )
    followers = [user.to_dict() for user in followers]
    return jsonify(followers)


@follow_api.route("/api/v1/follow", methods=["POST"])
@get_user_from_token(required=True)
def follow_user(user=None):
    """
    Follow or unfollow
    """
    payload = request.get_json()
    user_id = payload["id"]
    follow = payload["follow"]
    existing_follow = Follow.query.filter(
        Follow.follower_id == user['id'], Follow.user_id == user_id
    ).first()
    if existing_follow:
        existing_follow.active = follow
    else:
        db.session.add(
            Follow(follower_id=user['id'], user_id=user_id, active=True))
    db.session.commit()
    return "success"


def get_follower_count(user_id):
    follower_num = Follow.query.filter(
        Follow.user_id == user_id, Follow.active == True
    ).count()
    return follower_num


def get_following_count(user_id):
    following_num = Follow.query.filter(
        Follow.follower_id == user_id, Follow.active == True
    ).count()
    return following_num


def get_follows(user_id):
    """
    return:
    {
        followings: [1,2,3]
        followers: [1,2,3]
    }
    """
    follows = Follow.query.filter(Follow.active == True).filter(
        (Follow.follower_id == user_id) | (Follow.user_id == user_id)
    ).all()

    followings = []
    followers = []

    for f in follows:
        if f.user_id == user_id:
            followings.append(f.follower_id)
        else:
            followers.append(f.user_id)

    return followers, followings
