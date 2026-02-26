import json
from datetime import datetime
from typing import Optional

import redis.asyncio as aioredis

from ..utils import get_logger

logger = get_logger("traffic_guard")

_SNAPSHOTS_KEY = "tg:snapshots"
_ALERTS_KEY = "tg:alerts_count"
_HOURLY_STATS_KEY = "tg:hourly_stats"


class RedisCache:
    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        await self._redis.ping()
        logger.info("Redis connected")

    async def close(self):
        if self._redis:
            await self._redis.aclose()

    async def get_all_snapshots(self) -> dict[str, dict]:
        raw = await self._redis.hgetall(_SNAPSHOTS_KEY)
        return {username: self._deserialize(val) for username, val in raw.items()}

    async def get_snapshot(self, username: str) -> Optional[dict]:
        raw = await self._redis.hget(_SNAPSHOTS_KEY, username)
        if raw is None:
            return None
        return self._deserialize(raw)

    async def set_snapshots(self, snapshots: list[dict]):
        if not snapshots:
            return
        pipe = self._redis.pipeline()
        for snap in snapshots:
            pipe.hset(_SNAPSHOTS_KEY, snap["username"], self._serialize(snap))
        await pipe.execute()

    async def increment_alert_count(self, username: str) -> int:
        return await self._redis.hincrby(_ALERTS_KEY, username, 1)

    async def get_alert_count(self, username: str) -> int:
        val = await self._redis.hget(_ALERTS_KEY, username)
        return int(val) if val else 0

    async def save_hourly_stat(self, recorded_at: datetime, stats: dict) -> None:
        key = recorded_at.isoformat()
        await self._redis.hset(_HOURLY_STATS_KEY, key, self._serialize(stats))

    async def get_hourly_stats(self) -> dict[str, dict]:
        raw = await self._redis.hgetall(_HOURLY_STATS_KEY)
        return {key: json.loads(val) for key, val in raw.items()}

    @staticmethod
    def _serialize(data: dict) -> str:
        prepared = {}
        for k, v in data.items():
            if isinstance(v, datetime):
                prepared[k] = v.isoformat()
            else:
                prepared[k] = v
        return json.dumps(prepared)

    @staticmethod
    def _deserialize(raw: str) -> dict:
        data = json.loads(raw)
        for key in ("checked_at", "total_check_at"):
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key])
        return data
