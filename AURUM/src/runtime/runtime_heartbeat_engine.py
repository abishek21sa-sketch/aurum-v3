# src/runtime/runtime_heartbeat_engine.py

import json
from datetime import datetime, UTC
from pathlib import Path

from src.cache.cache_manager import CacheManager
from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("runtime.heartbeat")


RUNTIME_DIR = Path(config["runtime"]["output_dir"])
STATE_DIR = RUNTIME_DIR / "state"

GOVERNANCE_PATH = RUNTIME_DIR / "runtime_governance_decision.json"
MANIFEST_PATH = RUNTIME_DIR / "runtime_manifest.json"
DRIFT_PATH = RUNTIME_DIR / "runtime_drift_report.json"

HEARTBEAT_PATH = RUNTIME_DIR / "runtime_heartbeat.json"
HEARTBEAT_CACHE_KEY = "aurum:runtime:heartbeat"


def load_json(path: Path) -> dict:
    if not path.exists():
        logger.warning("Heartbeat source artifact missing: %s", path)
        return {}

    return json.loads(path.read_text(encoding="utf-8"))


def build_heartbeat() -> dict:
    governance = load_json(GOVERNANCE_PATH)
    manifest = load_json(MANIFEST_PATH)
    drift = load_json(DRIFT_PATH)

    system_status = manifest.get("system_status", {})

    heartbeat = {
        "heartbeat_timestamp_utc": datetime.now(UTC).isoformat(),
        "status": "alive",
        "environment": config["environment"],
        "runtime_directory": str(RUNTIME_DIR),
        "last_governance_decision": governance.get("decision", "UNKNOWN"),
        "last_governance_severity": governance.get("severity", "UNKNOWN"),
        "approved": governance.get("approved", False),
        "runtime_stable": system_status.get("runtime_stable", False),
        "pass_rate": system_status.get("pass_rate", 0.0),
        "failed_modules": system_status.get("failed_modules", None),
        "total_runtime_seconds": system_status.get("total_runtime_seconds", None),
        "drift_detected": drift.get("drift_detected", None),
        "drift_status": drift.get("severity", "UNKNOWN"),
    }

    logger.info(
        "Heartbeat built | status=%s | governance=%s | severity=%s | drift=%s | runtime_stable=%s",
        heartbeat["status"],
        heartbeat["last_governance_decision"],
        heartbeat["last_governance_severity"],
        heartbeat["drift_status"],
        heartbeat["runtime_stable"],
    )

    return heartbeat


def write_heartbeat_file(heartbeat: dict) -> None:
    HEARTBEAT_PATH.write_text(
        json.dumps(heartbeat, indent=2),
        encoding="utf-8",
    )

    logger.info("Saved runtime heartbeat file: %s", HEARTBEAT_PATH)


def write_heartbeat_cache(heartbeat: dict) -> None:
    cache = CacheManager()

    cache.set(
        HEARTBEAT_CACHE_KEY,
        heartbeat,
        ttl_seconds=config.get("cache", {}).get("default_ttl_seconds", 3600),
    )

    logger.info(
        "Saved runtime heartbeat to cache | key=%s | backend=%s",
        HEARTBEAT_CACHE_KEY,
        cache.backend_name,
    )


def write_heartbeat(heartbeat: dict) -> None:
    write_heartbeat_file(heartbeat)
    write_heartbeat_cache(heartbeat)


def main():
    logger.info("=" * 90)
    logger.info("AURUM RUNTIME HEARTBEAT ENGINE")
    logger.info("=" * 90)

    heartbeat = build_heartbeat()
    write_heartbeat(heartbeat)

    logger.info("Runtime heartbeat engine completed successfully.")


if __name__ == "__main__":
    main()