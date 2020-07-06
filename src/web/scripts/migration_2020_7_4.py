import json

from flask import Flask
# from flask_sqlalchemy import SQLAlchemy

from cfg.db import SQLALCHEMY_CONFIG
from models.user import User
from models.auth import Auth
from models.message import Message
from models import db


app = Flask(__name__)
FLASK_CONFIG = {**SQLALCHEMY_CONFIG}
app.config = {**app.config, **FLASK_CONFIG}
db.init_app(app)
app.app_context().push()


def migrate_messages():
    count = 0
    with open('/Users/swotong/Desktop/message.csv') as f:
        data = f.read()
        msgs = data.split('~newline~')
        for m in msgs:
            try:
                count = count + 1
                row_id, message, sender, receiver, created_at = m.split(
                    '~comma~')
                sender = int(sender)
                receiver = int(receiver)
                content = {
                    'type': 'text',
                    'value': message
                }
                content = json.dumps(content)
                msg = Message(message=content, created_at=created_at,
                              sender=sender, receiver=receiver)

                db.session.add(msg)
                if count % 100 == 0:
                    db.session.commit()
                    print(count)
            except Exception as e:
                print(e)

                pass
        db.session.commit()


migrate_messages()


def migrate_auths():
    count = 0
    with open('/Users/swotong/Desktop/auth.csv') as f:
        auths = f.readlines()
        for a in auths:
            count = count + 1
            row_id, user_id, pwd, uuid, created_at = a.split(',')
            auth = Auth(user_id=user_id, password=pwd)
            db.session.add(auth)
            if count % 100 == 0:
                db.session.commit()
                print(count)

        db.session.commit()


# migrate_auths()


def migrate_users():
    count = 0
    with open('/Users/swotong/Desktop/user.csv') as f:
        data = f.read()
        users = data.split('~newline~')
        for u in users:
            count = count + 1
            uuid, name, created_at, about, id, credit, last_checkin, has_avatar, role, block_until, room, mode = u.split(
                '~comma~')
            # print(u)
            name = name.replace('"', '')
            if about == 'NULL':
                about = None
            user = User(name=name, id=id, credit=int(credit),
                        about=about, role=int(role), avatar=int(has_avatar))

            db.session.add(user)
            if count % 100 == 0:
                db.session.commit()
                print(count)

        db.session.commit()
