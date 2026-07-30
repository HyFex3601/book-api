import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
redis_engine = redis.from_url(REDIS_URL)


