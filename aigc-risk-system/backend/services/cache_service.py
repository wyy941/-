from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import redis
from flask import current_app


@lru_cache(maxsize=1)
def _get_redis_client():
    redis_url = current_app.config.get("REDIS_URL")
    if not redis_url:
        return None

    try:
        return redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
        )
    except Exception:
        return None


def cache_get_json(key: str) -> Any | None:
    client = _get_redis_client()
    if client is None:
        return None

    try:
        payload = client.get(key)
        return json.loads(payload) if payload else None
    except Exception:
        return None


def cache_set_json(key: str, value: Any, ex: int | None = None) -> bool:
    client = _get_redis_client()
    if client is None:
        return False

    try:
        ttl = ex or current_app.config.get("CACHE_TTL_SECONDS", 120)
        client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        return True
    except Exception:
        return False


def cache_delete_prefix(prefix: str) -> int:
    client = _get_redis_client()
    if client is None:
        return 0

    deleted = 0
    try:
        for key in client.scan_iter(match=f"{prefix}*"):
            deleted += int(client.delete(key) or 0)
    except Exception:
        return 0
    return deleted
