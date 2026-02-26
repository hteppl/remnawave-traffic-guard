import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter

from ..config import Config
from ..utils import get_logger

logger = get_logger("traffic_guard")


class Notifier:
    def __init__(self, config: Config, bot: Bot):
        self._config = config
        self._bot = bot

    async def send_alert(self, text: str) -> bool:
        chat_id = self._config.telegram_chat_id.strip()
        if not chat_id:
            logger.warning("TELEGRAM_CHAT_ID is not set, skipping alert")
            return False

        try:
            kwargs = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }

            topic_id = self._config.telegram_topic_id.strip()
            if topic_id:
                try:
                    kwargs["message_thread_id"] = int(topic_id)
                except ValueError:
                    logger.warning(f"Invalid TELEGRAM_TOPIC_ID: {topic_id}")

            await self._bot.send_message(**kwargs)
            return True

        except TelegramRetryAfter as e:
            logger.warning(f"Flood control: waiting {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            return await self.send_alert(text)

        except TelegramForbiddenError:
            logger.error("Bot is blocked or has no access to chat")
            return False

        except TelegramBadRequest as e:
            error_msg = str(e).lower()
            if "chat not found" in error_msg:
                logger.error("Chat not found, check TELEGRAM_CHAT_ID")
            elif "message thread not found" in error_msg:
                logger.error("Thread not found, check TELEGRAM_TOPIC_ID")
            elif "bot is not a member" in error_msg:
                logger.error("Bot is not a member of the chat")
            else:
                logger.error(f"Telegram error: {e}")
            return False

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
