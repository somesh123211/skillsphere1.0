from dbutils.pooled_db import PooledDB
import pymysql

MYSQL_CONFIG = {
    "host": "YOUR_HOST",
    "user": "YOUR_USER",
    "password": "YOUR_PASSWORD",
    "database": "YOUR_DATABASE"
}

# 🔥 DB CONNECTION POOL
pool = PooledDB(
    creator=pymysql,
    maxconnections=10,      # max simultaneous connections
    mincached=2,            # idle connections kept ready
    maxcached=5,            # max idle connections
    blocking=True,          # wait if pool exhausted
    host=MYSQL_CONFIG["host"],
    user=MYSQL_CONFIG["user"],
    password=MYSQL_CONFIG["password"],
    database=MYSQL_CONFIG["database"],
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

def get_db():
    """
    Always returns a pooled connection.
    .close() will RETURN it to pool (not destroy).
    """
    return pool.connection()
