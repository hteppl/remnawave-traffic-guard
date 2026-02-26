from datetime import datetime, timedelta, timezone

import pytz

from ..api import RemnawaveClient
from ..config import Config
from ..db import RedisCache
from ..i18n import Translator
from ..notifications import Notifier
from ..utils import get_logger

logger = get_logger("traffic_guard")

GB = 1024 * 1024 * 1024


class TrafficMonitor:
    def __init__(
            self,
            config: Config,
            cache: RedisCache,
            remnawave: RemnawaveClient,
            notifier: Notifier,
            translator: Translator,
    ):
        self._config = config
        self._cache = cache
        self._remnawave = remnawave
        self._notifier = notifier
        self._t = translator

    async def check(self) -> dict | None:
        logger.info("Starting traffic check...")

        previous_snapshots = await self._cache.get_all_snapshots()
        current_users = await self._remnawave.fetch_all_users()

        if not current_users:
            logger.warning("Failed to fetch users from API")
            return None

        logger.info(f"Fetched {len(current_users)} users from API")

        tz = self._get_timezone()
        now = datetime.now(tz)
        now_utc = datetime.now(timezone.utc)
        time_str = now.strftime(self._config.time_format)
        today_str = now.strftime("%Y-%m-%d")
        yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

        min_traffic_bytes = self._config.min_traffic_gb * GB
        alerts_sent = 0
        snapshots_to_upsert: list[dict] = []
        seen_usernames: set[str] = set()

        active_users = 0
        total_traffic_bytes = 0
        top_user_username = ""
        top_user_tg_id = 0
        top_user_traffic_bytes = 0

        for user in current_users:
            username = user.get("username")
            user_uuid = user.get("uuid")
            if not username or username in seen_usernames:
                continue
            seen_usernames.add(username)

            current_traffic = user.get("lifetimeUsedTrafficBytes", 0) or 0
            tg_id = user.get("telegramId")
            if not tg_id:
                continue

            previous = previous_snapshots.get(username)

            traffic_diff = 0
            if previous:
                previous_traffic = previous.get("lifetime_traffic_bytes", 0) or 0
                traffic_diff = current_traffic - previous_traffic
                if traffic_diff > 0:
                    active_users += 1
                    total_traffic_bytes += traffic_diff
                    if traffic_diff > top_user_traffic_bytes:
                        top_user_traffic_bytes = traffic_diff
                        top_user_username = username
                        top_user_tg_id = tg_id

            if previous and self._config.interval_check_enabled:
                alerts_sent += await self._check_interval_spike(
                    previous, current_traffic, min_traffic_bytes, tg_id, username,
                    user_uuid, yesterday_str, today_str, time_str,
                )

            snapshot_data, total_alerts = await self._build_snapshot_and_check_total(
                username, tg_id, current_traffic, min_traffic_bytes, previous,
                now, now_utc, today_str, time_str, user_uuid,
            )
            alerts_sent += total_alerts
            snapshots_to_upsert.append(snapshot_data)

        await self._cache.set_snapshots(snapshots_to_upsert)

        total_traffic_gb = total_traffic_bytes / GB
        logger.info(
            f"Check complete. Processed: {len(seen_usernames)}, "
            f"active: {active_users}, traffic: {total_traffic_gb:.2f} GB, alerts: {alerts_sent}"
        )

        return {
            "total_users": len(seen_usernames),
            "active_users": active_users,
            "total_traffic_bytes": total_traffic_bytes,
            "top_user_username": top_user_username,
            "top_user_tg_id": top_user_tg_id,
            "top_user_traffic_bytes": top_user_traffic_bytes,
            "alerts_count": alerts_sent,
        }

    async def _check_interval_spike(
            self, previous: dict, current_traffic: int, min_traffic_bytes: float,
            tg_id: int, username: str, user_uuid: str | None,
            yesterday_str: str, today_str: str, time_str: str,
    ) -> int:
        previous_traffic = previous.get("lifetime_traffic_bytes", 0) or 0
        traffic_diff = current_traffic - previous_traffic

        if traffic_diff <= min_traffic_bytes:
            return 0

        traffic_diff_gb = traffic_diff / GB
        if traffic_diff_gb < self._config.interval_threshold_gb:
            return 0

        nodes_info_str = ""
        if user_uuid:
            nodes = await self._remnawave.fetch_user_nodes(
                user_uuid, yesterday_str, today_str, self._config.top_nodes_limit,
            )
            nodes_info_str = self._format_nodes_info(nodes, self._config.top_nodes_limit)

        alert_count = await self._cache.increment_alert_count(username)

        text = self._t.get(
            "traffic-spike",
            tg_id=str(tg_id),
            username=username,
            traffic_diff_gb=f"{traffic_diff_gb:.2f}",
            interval_minutes=str(self._config.check_interval_minutes),
            nodes_info=nodes_info_str,
            time=time_str,
            alert_count=str(alert_count),
        )

        await self._notifier.send_alert(text)
        logger.warning(
            f"Traffic spike: {username} +{traffic_diff_gb:.2f} GB in {self._config.check_interval_minutes} min (alert #{alert_count})")
        return 1

    async def _build_snapshot_and_check_total(
            self, username: str, tg_id: int, current_traffic: int, min_traffic_bytes: float,
            previous: dict | None, now: datetime, now_utc: datetime,
            today_str: str, time_str: str, user_uuid: str | None,
    ) -> tuple[dict, int]:
        snapshot = {
            "username": username,
            "tg_id": tg_id,
            "lifetime_traffic_bytes": current_traffic,
            "total_check_traffic_bytes": current_traffic,
            "total_check_at": now_utc,
        }

        if not previous or not self._config.total_check_enabled:
            return snapshot, 0

        total_check_at = previous.get("total_check_at")
        total_check_traffic = previous.get("total_check_traffic_bytes", 0) or 0

        if not total_check_at:
            return snapshot, 0

        if isinstance(total_check_at, str):
            total_check_at = datetime.fromisoformat(total_check_at)

        hours_passed = (now_utc - total_check_at).total_seconds() / 3600
        traffic_diff = current_traffic - total_check_traffic
        total_limit_exceeded = False
        alerts = 0

        if traffic_diff > min_traffic_bytes:
            traffic_diff_gb = traffic_diff / GB

            if traffic_diff_gb >= self._config.total_threshold_gb:
                total_limit_exceeded = True
                alerts = 1

                nodes_info_str = ""
                if user_uuid:
                    start_date = (now - timedelta(hours=self._config.total_check_hours)).strftime("%Y-%m-%d")
                    nodes = await self._remnawave.fetch_user_nodes(
                        user_uuid, start_date, today_str, self._config.top_nodes_limit,
                    )
                    nodes_info_str = self._format_nodes_info(nodes, self._config.top_nodes_limit)

                alert_count = await self._cache.increment_alert_count(username)

                text = self._t.get(
                    "total-limit",
                    tg_id=str(tg_id),
                    username=username,
                    traffic_gb=f"{traffic_diff_gb:.2f}",
                    hours=str(int(hours_passed)),
                    nodes_info=nodes_info_str,
                    time=time_str,
                    alert_count=str(alert_count),
                )

                await self._notifier.send_alert(text)
                logger.warning(
                    f"Total limit exceeded: {username} {traffic_diff_gb:.2f} GB in {int(hours_passed)} h (alert #{alert_count})")

        if total_limit_exceeded or hours_passed >= self._config.total_check_hours:
            snapshot["total_check_traffic_bytes"] = current_traffic
            snapshot["total_check_at"] = now_utc
        else:
            snapshot["total_check_traffic_bytes"] = total_check_traffic
            snapshot["total_check_at"] = total_check_at

        return snapshot, alerts

    def _get_timezone(self) -> pytz.BaseTzInfo:
        try:
            return pytz.timezone(self._config.timezone)
        except Exception:
            return pytz.UTC

    def _format_nodes_info(self, nodes: list[dict], limit: int = 5) -> str:
        if not nodes:
            return ""

        sorted_nodes = sorted(nodes, key=lambda x: x.get("total", 0), reverse=True)[:limit]
        if not sorted_nodes:
            return ""

        header = self._t.get("nodes-info-header")
        lines = [f"\n{header}\n"]
        for node in sorted_nodes:
            cc = node.get("country_code", "")
            flag = cc.upper() if cc and len(cc) == 2 else "--"

            name = node.get("name", "Unknown")
            traffic_gb = node.get("total", 0) / GB
            line = self._t.get("node-line", flag=flag, name=name, traffic_gb=f"{traffic_gb:.2f}")
            lines.append(f"{line}\n")

        return "".join(lines)
