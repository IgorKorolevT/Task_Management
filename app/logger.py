import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger = logging.getLogger("task_management")
logger.setLevel(LOG_LEVEL)
logger.propagate = False


if not logger.handlers:
    console_handler = logging.StreamHandler()

    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(LOG_LEVEL)

    file_handler = RotatingFileHandler(
        LOG_DIR / "task_management.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s "
        "- %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(LOG_LEVEL)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)