from datetime import datetime, timezone
import platform
import sys
import json

from src.infrastructure.config_loader import load_config, get_config_value
from src.infrastructure.storage_paths import RESULTS_DIR


RUNTIME_SUMMARY_PATH = RESULTS_DIR / "runtime" / "runtime_environment_summary.json"


def build_runtime_summary(environment: str | None = None) -> dict:
    config = load_config(environment)

    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": get_config_value(config, "project.name"),
        "environment": get_config_value(config, "project.environment"),
        "python_version": sys.version,
        "platform": platform.platform(),
        "database_enabled": get_config_value(config, "database.enabled"),
        "redis_enabled": get_config_value(config, "redis.enabled"),
        "tickers": get_config_value(config, "market_data.tickers"),
        "lookback_days": get_config_value(config, "market_data.lookback_days"),
        "pipeline_fail_fast": get_config_value(config, "pipeline.fail_fast"),
        "pipeline_save_artifacts": get_config_value(config, "pipeline.save_artifacts"),
    }


def save_runtime_summary(environment: str | None = None) -> dict:
    summary = build_runtime_summary(environment)
    RUNTIME_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    with RUNTIME_SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    return summary


if __name__ == "__main__":
    summary = save_runtime_summary()
    print("RUNTIME ENVIRONMENT SUMMARY SAVED")
    print(f"Path: {RUNTIME_SUMMARY_PATH}")
    print(json.dumps(summary, indent=4))
