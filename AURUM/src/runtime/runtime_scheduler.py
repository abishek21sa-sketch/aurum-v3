# src/runtime/runtime_scheduler.py

import subprocess
import sys
from datetime import datetime, UTC

from apscheduler.schedulers.blocking import BlockingScheduler

from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("runtime.scheduler")


def run_institutional_runtime() -> None:
    logger.info("=" * 90)
    logger.info("SCHEDULED AURUM INSTITUTIONAL RUNTIME STARTED")
    logger.info("=" * 90)

    start = datetime.now(UTC)

    result = subprocess.run(
        [sys.executable, "-m", "scripts.run_institutional_runtime"],
        text=True,
    )

    end = datetime.now(UTC)
    runtime_seconds = (end - start).total_seconds()

    if result.returncode == 0:
        logger.info(
            "Scheduled institutional runtime completed successfully | runtime_seconds=%.4f",
            runtime_seconds,
        )
    else:
        logger.error(
            "Scheduled institutional runtime failed | return_code=%s | runtime_seconds=%.4f",
            result.returncode,
            runtime_seconds,
        )


def main():
    logger.info("=" * 90)
    logger.info("AURUM RUNTIME SCHEDULER")
    logger.info("=" * 90)

    scheduler_config = config.get("scheduler", {})

    interval_minutes = scheduler_config.get("interval_minutes", 60)
    timezone = scheduler_config.get("timezone", "UTC")
    run_immediately = scheduler_config.get("run_immediately", True)

    scheduler = BlockingScheduler(timezone=timezone)

    scheduler.add_job(
        run_institutional_runtime,
        trigger="interval",
        minutes=interval_minutes,
        id="aurum_institutional_runtime",
        replace_existing=True,
        next_run_time=datetime.now(UTC) if run_immediately else None,
    )

    logger.info(
        "Runtime scheduler started | interval_minutes=%s | timezone=%s | run_immediately=%s",
        interval_minutes,
        timezone,
        run_immediately,
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.warning("Runtime scheduler stopped manually.")


if __name__ == "__main__":
    main()