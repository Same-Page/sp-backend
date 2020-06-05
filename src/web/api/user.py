from datetime import datetime, date, timedelta

from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc, and_

from models import db
from models.user import User
from models.follow import Follow
from api.follow import get_follower_count, get_following_count
from api.auth import Account
from sp_token import get_user_from_token
from sp_token.tokens import revoke_all_tokens_of_user, refresh_user_data

from clients.s3 import upload_file

user_api = Blueprint("User", __name__)

THANK_WAIT_TIME = 60*60
THANK_WAIT_TIME_MOD = 60*5

# below two endpoint for user themself
@user_api.route("/api/v1/user", methods=["GET"])
@get_user_from_token(True)
def user_from_token(user=None):
    '''
    Used by socket server to check user's token
    and get basic user data
    If we move token management to separate service,
    e.g. elasticcache, we won't need this endpoint maybe
    '''
    return jsonify(user)


@user_api.route("/api/v1/user", methods=["POST"])
@get_user_from_token(True)
def update_user(user=None):
    name = request.form.get("name")
    email = request.form.get("email")
    about = request.form.get("about")
    website = request.form.get("website")
    avatar = request.files.get("avatar")

    u = User.query.filter_by(id=user['id']).first()

    if email != u.email:
        # if updating email, ensure new email isn't already registered
        email_registered_by_user = User.query.filter_by(email=email).first()
        if email_registered_by_user:
            return jsonify({"error": "email registed already!"}), 409

    if avatar:
        u.has_avatar = u.has_avatar + 1
        upload_file(avatar, f"{u.id}.jpg")

    u.name = name
    u.about = about
    u.website = website
    u.email = email

    # User.query.filter_by(id=user.id).update(
    #     {"name": user.name, "about": user.about, "has_avatar": user.has_avatar}
    # )

    db.session.commit()
    token = request.headers.get("token")
    account_data = Account(token, u.to_dict(return_email=True)).to_dict()
    refresh_user_data(token, u)
    return jsonify(account_data)


# Endpoints below for getting other user rather than self


@user_api.route("/api/v1/user/<int:user_id>", methods=["GET"])
@get_user_from_token(True)
def get_user_from_id(user_id, user=None):
    # should not be used to get self data
    # use account login to get self data
    res = User.query.filter_by(id=user_id).first()

    res = res.to_dict(return_email=False)

    res["followerCount"] = get_follower_count(user_id)
    res["followingCount"] = get_following_count(user_id)

    # check if login user is following or followed by target user
    res['isFollowing'] = False
    res['isFollower'] = False
    follows = Follow.query.filter(Follow.active == True).filter(
        and_(Follow.follower_id == user_id, Follow.user_id == user['id']) |
        and_(Follow.user_id == user_id, Follow.follower_id == user['id'])
    ).all()

    for f in follows:
        if f.user_id == user['id']:
            res['isFollower'] = True
        # count follow self as well
        if f.follower_id == user['id']:
            res['isFollowing'] = True

    return jsonify(res)


@user_api.route("/api/v1/latest_users", methods=["GET"])
@get_user_from_token(False)
def get_latest_users(user=None):
    users = User.query.order_by(
        desc(User.id)).limit(10)
    return jsonify([u.to_dict() for u in users])


@user_api.route("/api/v1/thank_user", methods=["POST"])
@get_user_from_token(True)
def thank_user(user=None):

    payload = request.get_json()
    user_id = payload["userId"]
    if str(user_id) == str(user['numId']):
        return "not for yourself", 400
    # Check time, set time

    user = User.query.filter_by(id=user['id']).first()
    time_elapse = datetime.now() - user.last_checkin

    thank_wait_time = THANK_WAIT_TIME
    if user.is_mod():
        thank_wait_time = THANK_WAIT_TIME_MOD

    if time_elapse.seconds < thank_wait_time:
        return "Too soon", 429

    target_user = User.query.filter_by(id=user_id).first()
    target_user.credit = target_user.credit + 3
    user.credit = user.credit + 1
    user.last_checkin = datetime.now()
    db.session.commit()
    # TODO: refresh user and target user data in cache

    return jsonify({'credit': user.credit})


# Below endpoints are used by mod and admin
@user_api.route("/api/v1/block_user", methods=["POST"])
@get_user_from_token(True)
def block_user(user=None):
    if not user['isMod']:
        return jsonify("No permission"), 403
    payload = request.get_json()
    user_id = payload["userId"]
    block_until = date.today() + timedelta(3)
    target_user = User.query.filter_by(id=user_id).first()
    if target_user.role >= user['role']:
        return jsonify("Target user has higher permission"), 409

    target_user.block_until = block_until
    db.session.commit()
    # Delete token
    revoke_all_tokens_of_user(user_id)
    return jsonify(f"Block until {block_until}")


@user_api.route("/api/v1/unblock_user", methods=["POST"])
@get_user_from_token(True)
def unblock_user(user=None):
    if not user['isMod']:
        return jsonify("No permission"), 403

    payload = request.get_json()
    user_id = payload["userId"]
    target_user = User.query.filter_by(id=user_id).first()
    if target_user.role >= user['role']:
        return jsonify("Target user has higher permission"), 409

    target_user.block_until = None
    db.session.commit()
    return jsonify(f"unblocked")


@user_api.route("/api/v1/user/check_email_registered", methods=["POST"])
def check_email_registered():
    payload = request.get_json()
    email = payload["email"]

    user = User.query.filter_by(email=email).first()
    registered = True if user else False
    return jsonify({
        "registered": registered
    })
