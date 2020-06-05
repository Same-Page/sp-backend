import copy
import json

from flask import Blueprint, request, jsonify
from sqlalchemy.sql import func
from sqlalchemy import desc, text

from models.comment import Comment
from models.user import User
from models.vote import Vote
from models import db
from cfg.urls import cloud_front
from sp_token import get_user_from_token

TOP_K_LIKED_COMMENT = 3

comment_api = Blueprint("Comment", __name__)


@comment_api.route("/api/v1/comment", methods=["POST"])
@get_user_from_token(required=True)
def post_comment(user=None):

    payload = request.get_json()
    url = payload["url"]

    # TODO: sanitize input
    content = payload["content"]
    # TODO: check file type, hard code to image for now
    if content['type'] == 'file':
        content['type'] = 'image'
    content = json.dumps(content)
    # TODO: camel case from frontend
    # reply_to_user_id = payload.get("replay_to_user_id")
    # reply_to_user_name = payload.get("replay_to_user_name")

    # if reply_to_user_id:
    #     content = "@" + reply_to_user_name + "\n" + content
    # TODO: send notification

    db_comment = Comment(url=url, content=content, user_id=user['id'])
    db.session.add(db_comment)
    db.session.commit()
    comment_obj = CommentObj(db_comment.to_dict(), user)
    return jsonify(comment_obj.to_dict())


@comment_api.route("/api/v1/comment/vote", methods=["POST"])
@get_user_from_token(required=True)
def vote_comment(user=None):

    payload = request.get_json()
    comment_id = payload["commentId"]
    score = payload["score"]  # 1/-1/0

    existing_vote = Vote.query.filter(
        Vote.comment_id == comment_id, Vote.user_id == user['id']
    ).first()
    if existing_vote:
        existing_vote.score = score
    else:
        db.session.add(Vote(comment_id=comment_id,
                            user_id=user['id'], score=score))
    db.session.commit()
    return "success"


# @comment_api.route("/api/v1/latest_comments", methods=["GET"])
# @get_user_from_token(required=False)
# def get_latest_comments(user=None):
#     res = (
#         db.session.query(Comment, User)
#         .join(User)
#         .order_by(desc(Comment.id))
#         .group_by(User)
#         # .filter(User.has_avatar)
#         .limit(10)
#         .all()
#     )
#     comments = []
#     for comment, commenter in res:
#         comments.append({
#             "id": comment.id,
#             "url": comment.url,
#             "content": comment.content,
#             "created_at": comment.created_at,
#             "user": commenter.to_dict(),
#             "self": True if (user and str(commenter.id) == str(user['id'])) else False,
#         })

#     return jsonify(comments)


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

    comments_dict = {}

    # Get commenters and comments first
    user_comment_rows = db.session.query(User, Comment).filter(
        User.id == Comment.user_id).filter(Comment.url == url).order_by(Comment.id.desc()).all()

    for commenter, comment in user_comment_rows:
        comments_dict[comment.id] = {
            'comment': comment,
            'commenter': commenter
        }

    # Then count likes/dislikes
    like_rows = db.session.query(Comment.id, func.count(Vote.id)).join(
        Vote, Vote.comment_id == Comment.id).filter(Comment.url == url).filter(Vote.score > 0).group_by(Comment.id).all()

    for c_id, like_count in like_rows:
        comments_dict[c_id]['like_count'] = like_count

    dislike_rows = db.session.query(Comment.id, func.count(Vote.id)).join(
        Vote, Vote.comment_id == Comment.id).filter(Comment.url == url).filter(Vote.score < 0).group_by(Comment.id).all()

    for c_id, dislike_count in dislike_rows:
        comments_dict[c_id]['dislike_count'] = dislike_count

    # Get user's votes for this url if logged in
    if user:
        user_votes = db.session.query(Vote).join(
            Comment, Comment.id == Vote.comment_id).filter(Vote.user_id == user['id']).filter(Comment.url == url).all()
        for v in user_votes:
            comments_dict[v.comment_id]['my_score'] = v.score

    res = []
    for comment_dict in comments_dict.values():
        comment_obj = CommentObj(comment_dict['comment'].to_dict(), comment_dict['commenter'].to_dict(), comment_dict.get(
            'like_count'), comment_dict.get('dislike_count'), comment_dict.get('my_score'))
        res.append(comment_obj.to_dict())

    # default ordering is top 3 most liked then by time DESC
    if order == 'latest':
        final_res = res
    else:
        res = sorted(res, key=lambda c: c['like_count'], reverse=True)
        top_comments = res[:TOP_K_LIKED_COMMENT]
        rest_comments = res[TOP_K_LIKED_COMMENT:]
        rest_comments = sorted(
            rest_comments, key=lambda c: c['id'], reverse=True)
        final_res = top_comments + rest_comments
    return jsonify(final_res)


class CommentObj:
    """
    Comment model to send to client, not db model
    """

    def __init__(self, comment, commenter, like_count=0, dislike_count=0, my_score=0):
        """
        comment and commenter are dict not object because post comment only has
        user dict not user object... TODO: that decorator should return user object?
        score means if current user like or dislike this comment
        value is one of -1, 0, 1
        """
        self.comment = comment
        self.commenter = commenter
        self.like_count = like_count
        self.dislike_count = dislike_count
        self.my_score = my_score

    def to_dict(self):
        res = copy.deepcopy(self.comment)
        res['content'] = json.loads(self.comment['content'])

        res['user'] = self.commenter
        res['like_count'] = self.like_count or 0
        res['dislike_count'] = self.dislike_count or 0
        res['my_score'] = self.my_score or 0
        return res
