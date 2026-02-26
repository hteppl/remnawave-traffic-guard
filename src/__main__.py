import asyncio
import signal

from aiogram import Bot

from .api import RemnawaveClient
from .config import Config
from .db import RedisCache
from .i18n import Translator
from .monitoring import HourlyStatsCollector, TrafficMonitor
from .notifications import Notifier
from .utils import setup_logger

logger = setup_logger("traffic_guard")


class TrafficGuard:
    def __init__(self, config: Config):
        self._config = config
        self._shutdown_event = asyncio.Event()
        self._check_lock = asyncio.Lock()

        self._cache = RedisCache(config.redis_url)
        self._remnawave = RemnawaveClient(config.remnawave_api_url, config.remnawave_api_key, config.api_page_size)
        self._bot = Bot(token=config.telegram_bot_token)
        self._notifier = Notifier(config, self._bot)
        self._translator = Translator(config.language)
        self._monitor = TrafficMonitor(config, self._cache, self._remnawave, self._notifier, self._translator)
        self._hourly = HourlyStatsCollector(config, self._cache, self._notifier, self._translator)

    async def start(self):
        self._register_signals()
        logger.info("Initializing...")

        await self._cache.connect()
        await self._send_startup_message()

        interval = self._config.check_interval_minutes * 60
        logger.info(f"Starting check loop (every {self._config.check_interval_minutes} min)")

        try:
            while not self._shutdown_event.is_set():
                if not self._check_lock.locked():
                    async with self._check_lock:
                        try:
                            metrics = await self._monitor.check()
                            if metrics and self._config.hourly_stats_enabled:
                                self._hourly.accumulate(metrics)
                                await self._hourly.maybe_flush()
                        except Exception as e:
                            logger.error(f"Check loop error: {e}")

                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=interval)
                    break
                except asyncio.TimeoutError:
                    if self._config.hourly_stats_enabled:
                        self._hourly.log_progress()
        finally:
            await self._shutdown()

    async def _shutdown(self):
        logger.info("Shutting down...")
        await self._remnawave.close()
        await self._cache.close()
        await self._bot.session.close()
        logger.info("Stopped")

    async def _send_startup_message(self):
        text = self._translator.get(
            "service-started",
            interval=str(self._config.check_interval_minutes),
            interval_threshold=str(self._config.interval_threshold_gb),
            total_threshold=str(self._config.total_threshold_gb),
            total_hours=str(self._config.total_check_hours),
            language=self._config.language,
        )
        await self._notifier.send_alert(text)

    def _register_signals(self):
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._handle_signal)

    def _handle_signal(self):
        logger.info("Shutdown signal received")
        self._shutdown_event.set()


async def main():
    config = Config.from_env()
    app = TrafficGuard(config)
    await app.start()


if __name__ == "__main__":
    asyncio.run(main())
