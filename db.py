import os
import pymysql
from dbutils.pooled_db import PooledDB

# ------------------------------------------------------------------
# IMPORTANT:
# - Environment variables MUST be loaded BEFORE this file is imported
# - app.py must call load_dotenv() at the very top
# ------------------------------------------------------------------

# Optional debug (comment out after first successful run)


# ------------------------------------------------------------------
# DB CONNECTION POOL
# ------------------------------------------------------------------
pool = PooledDB(
    creator=pymysql,
    maxconnections=5,      # Max total connections
    mincached=1,            # Do NOT pre-create connections (safe startup)
    maxcached=2,            # Max idle connections
    blocking=True,          # Wait if pool is exhausted
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DB"),
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

def get_db():
    """
    Returns a pooled database connection.
    Calling .close() will RETURN the connection to the pool.
    """
    return pool.connection()
