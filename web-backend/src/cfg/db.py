import os
import sqlite3
from pathlib import Path


if os.environ.get('MYSQL_USER'):
    # if using a mysql database
    DB = {
        "driver": "mysql+pymysql",
        "user": os.environ['MYSQL_USER'],
        "password": os.environ['MYSQL_PASSWORD'],
        "host": os.environ['MYSQL_HOST'],
        "db": os.environ['MYSQL_DB'],
    }

    DB_URI = "{driver}://{user}:{password}@{host}/{db}?charset=utf8mb4".format(
        **DB)

    SQLALCHEMY_CONFIG = {
        "SQLALCHEMY_DATABASE_URI": DB_URI,
        "SQLALCHEMY_POOL_SIZE": 50,
        "SQLALCHEMY_POOL_RECYCLE": 600,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,  # Saves a lot of space during migs
    }

else:
    # db file is not included in the repo, first time
    # run will create the file in user's directory
    # all tables will be created

    SQLITE_FILE_PATH = 'db/sqlite/sp.db'
    if not os.path.isfile(SQLITE_FILE_PATH):
        Path(SQLITE_FILE_PATH).touch()
        try:
            qry = open('db/sqlite/create_tables.sql', 'r').read()
            conn = sqlite3.connect(SQLITE_FILE_PATH)
            c = conn.cursor()
            c.executescript(qry)
            conn.commit()
            c.close()
            conn.close()
        except Exception as e:
            os.remove(SQLITE_FILE_PATH)
            raise e

    SQLALCHEMY_CONFIG = {
        "SQLALCHEMY_DATABASE_URI": f'sqlite:///{SQLITE_FILE_PATH}',
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    }
