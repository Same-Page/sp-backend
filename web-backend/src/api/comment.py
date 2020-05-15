from flask import Blueprint, request, jsonify
from sqlalchemy.sql import func
from sqlalchemy import desc, text

from models.comment import Comment
from models.user import User
from models.vote import Vote
from models import db
from sp_token.tokens import create_token
from cfg.urls import cloud_front
from sp_token import get_user_from_token


comment_api = Blueprint("Comment", __name__)


@comment_api.route("/api/v1/comment", methods=["POST"])
@get_user_from_token(required=True)
def post_comment(user=None):

    payload = request.get_json()
    # TODO: sanitize input
    url = payload["url"]
    content = payload["content"]
    reply_to_user_id = payload.get("replay_to_user_id")
    reply_to_user_name = payload.get("replay_to_user_name")

    if reply_to_user_id:
        content = "@" + reply_to_user_name + "\n" + content
        # TODO: send notification

    # Because when getting comments, we join on user.id, so we also need to
    # save with user.id here
    db_comment = Comment(url=url, content=content, user_id=user['id'])
    db.session.add(db_comment)
    db.session.commit()
    comment = CommentObj(db_comment.id, db_comment.content,
                         db_comment.created_at, 0, user, False, True)
    return jsonify([comment.to_dict()])


@comment_api.route("/api/v1/vote_comment", methods=["POST"])
@get_user_from_token(required=True)
def vote_comment(user=None):

    payload = request.get_json()
    comment_id = payload["comment_id"]

    existing_vote = Vote.query.filter(
        Vote.comment_id == comment_id, Vote.user_id == user['id']
    ).first()
    if existing_vote:
        existing_vote.score = 1 if existing_vote.score == 0 else 0
    else:
        db.session.add(Vote(comment_id=comment_id,
                            user_id=user['id'], score=1))
    db.session.commit()
    return "success"


@comment_api.route("/api/v1/latest_comments", methods=["GET"])
@get_user_from_token(required=False)
def get_latest_comments(user=None):
    res = (
        db.session.query(Comment, User)
        .join(User)
        .order_by(desc(Comment.id))
        .group_by(User)
        # .filter(User.has_avatar)
        .limit(10)
        .all()
    )
    comments = []
    for comment, commenter in res:
        comments.append({
            "id": comment.id,
            "url": comment.url,
            "content": comment.content,
            "created_at": comment.created_at,
            "user": commenter.to_dict(),
            "self": True if (user and str(commenter.id) == str(user['id'])) else False,
        })

    return jsonify(comments)


@comment_api.route("/api/v1/get_comments", methods=["POST"])
@get_user_from_token(required=False)
def get_comments(user=None):
    """
    Make it a POST endpoint because url in url param
    often cause problem
    """
    payload = request.get_json()
    url = payload["url"]
    limit = payload.get("limit", 30)
    order = payload.get("order")
    offset = payload.get("offset", 0)

    orderBy = "score Desc, "
    if order == "newest":
        orderBy = ""

    query_str = f"SELECT comment.id, comment.content, comment.user_id, comment.created_at,\
        user.id, user.name, user.has_avatar, SUM(vote.score) as score FROM comment \
        LEFT JOIN vote on vote.comment_id = comment.id \
        LEFT JOIN user on comment.user_id = user.id \
        WHERE comment.url = '{url}' GROUP BY comment.id ORDER BY {orderBy} comment.created_at DESC LIMIT {offset}, {limit}"

    res = db.engine.execute(text(query_str))

    # Get user's votes for this url
    user_voted_comments = []
    if user:
        user_votes = Vote.query.filter(
            Vote.user_id == user['id'], Vote.score == 1)
        user_voted_comments = [vote.comment_id for vote in user_votes]

    # comment.user_id is uuid (zxcvjohsudaf) in the past
    # therefore we also get user.id and return to client
    # In the future, uuid will be the same as user.id
    # avatar image is always {uuid}.jpg
    comments = []
    for row in res:
        id, content, uuid, created_at, user_id, name, has_avatar, score = row

        if has_avatar:
            avatar_src = f"{cloud_front}{uuid}.jpg?v={has_avatar}"
        else:
            avatar_id = user_id % 150
            avatar_src = f"{cloud_front}avatar/{avatar_id}.jpg"

        comment_user = {
            'id': user_id,
            'name': name,
            'avatarSrc': avatar_src
        }
        comment = CommentObj(id, content, created_at, score, comment_user,
                             id in user_voted_comments, user and str(user['id']) == str(user_id))
        comments.append(comment.to_dict())

    return jsonify(comments)


class CommentObj:
    """
    Comment model to send to client, not db model
    """

    def __init__(self, id, content, created_at, score, user, voted, own_comment):
        self.id = id
        self.content = content
        self.created_at = created_at
        self.score = score
        self.user = user
        self.voted = voted
        self.own_comment = own_comment

    def to_dict(self):
        return {
            'id': self.id,
            'content': {
                'value': self.content,
                'type': 'text'
            },
            'created_at': self.created_at,
            'score': self.score,
            'user': self.user,
            'voted': self.voted,
            'self': self.own_comment

        }
