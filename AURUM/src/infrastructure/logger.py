import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.infrastructure.storage_paths import RESULTS_DIR


LOG_DIR = RESULTS_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(
    logger_name: str,
    log_filename: str | None = None,
    level: int = logging.INFO,
) -> logging.Logger:

    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    if log_filename:
        file_path = LOG_DIR / log_filename

        file_handler = RotatingFileHandler(
            filename=file_path,
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8",
        )

        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    logger.propagate = False

    return logger


if __name__ == "__main__":
    logger = get_logger(
        logger_name="aurum_test_logger",
        log_filename="aurum_test.log",
    )

    logger.info("AURUM logging system initialized.")
    logger.warning("This is a warning test.")
    logger.error("This is an error test.")
