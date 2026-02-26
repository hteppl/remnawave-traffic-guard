from datetime import datetime

import pytz

from ..config import Config
from ..db import RedisCache
from ..i18n import Translator
from ..notifications import Notifier
from ..utils import get_logger

logger = get_logger("traffic_guard")

GB = 1024 * 1024 * 1024


class HourlyStatsCollector:
    def __init__(
        self,
        config: Config,
        cache: RedisCache,
        notifier: Notifier,
        translator: Translator,
    ):
        self._config = config
        self._cache = cache
        self._notifier = notifier
        self._translator = translator

        self._stats = self._empty_stats()
        self._current_hour = self._get_current_hour()

    def accumulate(self, metrics: dict) -> None:
        s = self._stats
        s["checks_count"] += 1
        s["total_users"] = max(s["total_users"], metrics["total_users"])
        s["active_users"] += metrics["active_users"]
        s["total_traffic_bytes"] += metrics["total_traffic_bytes"]
        s["alerts_count"] += metrics["alerts_count"]
        if metrics["top_user_traffic_bytes"] > s["top_user_traffic_bytes"]:
            s["top_user_traffic_bytes"] = metrics["top_user_traffic_bytes"]
            s["top_user_username"] = metrics["top_user_username"]
            s["top_user_tg_id"] = metrics["top_user_tg_id"]

    async def maybe_flush(self) -> None:
        current_hour = self._get_current_hour()
        if current_hour <= self._current_hour:
            return

        stats = self._stats
        if stats["checks_count"] == 0:
            self._current_hour = current_hour
            return

        hour_boundary = self._current_hour
        time_str = hour_boundary.strftime(self._config.time_format)

        total_traffic_gb = stats["total_traffic_bytes"] / GB
        top_user_traffic_gb = stats["top_user_traffic_bytes"] / GB

        text = self._translator.get(
            "hourly-stats",
            total_users=str(stats["total_users"]),
            active_users=str(stats["active_users"]),
            total_traffic_gb=f"{total_traffic_gb:.2f}",
            top_user_username=stats["top_user_username"] or "—",
            top_user_traffic_gb=f"{top_user_traffic_gb:.2f}",
            alerts_count=str(stats["alerts_count"]),
            time=time_str,
        )
        await self._notifier.send_alert(text)
        await self._cache.save_hourly_stat(hour_boundary, stats)

        self._stats = self._empty_stats()
        self._current_hour = current_hour
        logger.info(f"Hourly stats sent for {time_str}")

    def log_progress(self) -> None:
        if self._stats["checks_count"] == 0:
            return
        traffic_gb = self._stats["total_traffic_bytes"] / GB
        logger.info(
            f"Hourly stats so far — traffic: {traffic_gb:.2f} GB, "
            f"active users: {self._stats['active_users']}, "
            f"alerts: {self._stats['alerts_count']}, "
            f"checks: {self._stats['checks_count']}"
        )

    def _get_current_hour(self) -> datetime:
        try:
            tz = pytz.timezone(self._config.timezone)
        except Exception:
            tz = pytz.UTC
        now = datetime.now(tz)
        return now.replace(minute=0, second=0, microsecond=0)

    @staticmethod
    def _empty_stats() -> dict:
        return {
            "total_users": 0,
            "active_users": 0,
            "total_traffic_bytes": 0,
            "top_user_username": "",
            "top_user_tg_id": 0,
            "top_user_traffic_bytes": 0,
            "alerts_count": 0,
            "checks_count": 0,
        }
