import os
import redis

redisConnPool = redis.ConnectionPool(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))