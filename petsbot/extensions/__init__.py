import os
import redis

redis_connection_pool = redis.ConnectionPool(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))