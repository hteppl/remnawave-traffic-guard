import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    remnawave_api_url: str = ""
    remnawave_api_key: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_topic_id: str = ""

    interval_check_enabled: bool = True
    check_interval_minutes: int = 10
    interval_threshold_gb: float = 20.0

    total_check_enabled: bool = True
    total_check_hours: int = 24
    total_threshold_gb: float = 100.0

    min_traffic_gb: float = 0.5
    top_nodes_limit: int = 5
    api_page_size: int = 1000
    api_batch_delay: float = 1.0

    hourly_stats_enabled: bool = True

    language: str = "en"
    timezone: str = "Europe/Moscow"
    time_format: str = "%d.%m.%Y %H:%M:%S"

    redis_url: str = "redis://redis:6379/0"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            remnawave_api_url=os.getenv("REMNAWAVE_API_URL", ""),
            remnawave_api_key=os.getenv("REMNAWAVE_API_KEY", ""),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            telegram_topic_id=os.getenv("TELEGRAM_TOPIC_ID", ""),
            interval_check_enabled=os.getenv("INTERVAL_CHECK_ENABLED", "true").lower() == "true",
            check_interval_minutes=int(os.getenv("CHECK_INTERVAL_MINUTES", "10")),
            interval_threshold_gb=float(os.getenv("INTERVAL_THRESHOLD_GB", "20")),
            total_check_enabled=os.getenv("TOTAL_CHECK_ENABLED", "true").lower() == "true",
            total_check_hours=int(os.getenv("TOTAL_CHECK_HOURS", "24")),
            total_threshold_gb=float(os.getenv("TOTAL_THRESHOLD_GB", "100")),
            min_traffic_gb=float(os.getenv("MIN_TRAFFIC_GB", "0.5")),
            top_nodes_limit=int(os.getenv("TOP_NODES_LIMIT", "5")),
            api_page_size=min(int(os.getenv("API_PAGE_SIZE", "1000")), 1000),
            api_batch_delay=float(os.getenv("API_BATCH_DELAY", "1.0")),
            hourly_stats_enabled=os.getenv("HOURLY_STATS_ENABLED", "true").lower() == "true",
            language=os.getenv("LANGUAGE", "en"),
            timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
            time_format=os.getenv("TIME_FORMAT", "%d.%m.%Y %H:%M:%S"),
            redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        )
