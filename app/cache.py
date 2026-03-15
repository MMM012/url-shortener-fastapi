import os
import redis
from redis.exceptions import ConnectionError

REDIS_URL = os.getenv("REDIS_URL")


class DummyCache:
    def get(self, key: str):
        return None

    def set(self, key: str, value: str, ex: int | None = None):
        pass

    def delete(self, key: str):
        pass


if REDIS_URL:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
else:
    redis_client = DummyCache()


def get_link_cache_key(short_code: str) -> str:
    return f"link:{short_code}"
