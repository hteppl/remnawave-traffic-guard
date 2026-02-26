import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_MAX_BYTES = 20 * 1024 * 1024  # 20 MB
_LOG_BACKUP_COUNT = 3


def setup_logger(name: str, level: str = "INFO", log_file: str = None):
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.handlers = []

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    http_level = logging.DEBUG if level.upper() == "DEBUG" else logging.WARNING
    logging.getLogger("httpx").setLevel(http_level)
    logging.getLogger("httpcore").setLevel(http_level)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=_LOG_MAX_BYTES,
            backupCount=_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logger = logging.getLogger(name)
    return logger


def get_logger(name: str):
    return logging.getLogger(name)
