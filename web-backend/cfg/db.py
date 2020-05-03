import os

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
    "SQLALCHEMY_POOL_RECYCLE": 600,
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,  # Saves a lot of space during migs
}
