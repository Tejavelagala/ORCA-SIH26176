import json
import os
from typing import Optional

_memory_cache = {}

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

REDIS_URL = os.getenv("REDIS_URL", "").strip()

async def get_json(key: str) -> Optional[dict]:
    if REDIS_URL and redis:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        try:
            value = await client.get(key)
            return json.loads(value) if value else None
        finally:
            await client.aclose()
    value = _memory_cache.get(key)
    return json.loads(value) if value else None

async def set_json(key: str, value: dict, ttl_seconds: int = 300) -> None:
    encoded = json.dumps(value, default=str)
    if REDIS_URL and redis:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        try:
            await client.set(key, encoded, ex=ttl_seconds)
        finally:
            await client.aclose()
        return
    _memory_cache[key] = encoded

def cache_key(query: str, location: str, language: str) -> str:
    normalized = "|".join([
        (query or "").strip().lower(),
        (location or "").strip().lower(),
        (language or "en-IN").strip(),
    ])
    return "orca:v1:" + str(abs(hash(normalized)))
