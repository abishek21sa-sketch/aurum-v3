# src/logging/runtime_logger.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config.config_loader import load_config


config = load_config()

LOG_DIR = Path(config["runtime"]["output_dir"]) / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = config.get("logging", {}).get("level", "INFO").upper()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVEL)

    file_handler = RotatingFileHandler(
        LOG_DIR / "aurum_runtime.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


if __name__ == "__main__":
    logger = get_logger("aurum.test")
    logger.info("Runtime logger initialized successfully.")
    logger.warning("Runtime logger warning test.")
    logger.error("Runtime logger error test.")