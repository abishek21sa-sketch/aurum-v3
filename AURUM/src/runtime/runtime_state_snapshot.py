# src/runtime/runtime_state_snapshot.py

import json
from datetime import datetime, UTC
from pathlib import Path

from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("runtime.state_snapshot")


RUNTIME_DIR = Path(config["runtime"]["output_dir"])
STATE_DIR = RUNTIME_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = RUNTIME_DIR / "runtime_manifest.json"
GOVERNANCE_PATH = RUNTIME_DIR / "runtime_governance_decision.json"
CHECKPOINT_PATH = RUNTIME_DIR / "runtime_checkpoint_summary.csv"
HEALTH_PATH = RUNTIME_DIR / "runtime_health_summary.csv"

LATEST_SNAPSHOT_PATH = STATE_DIR / "latest_runtime_state.json"
REGISTRY_PATH = STATE_DIR / "runtime_state_registry.jsonl"


def load_json(path: Path) -> dict:
    if not path.exists():
        logger.error("Required JSON artifact missing: %s", path)
        raise FileNotFoundError(f"Missing required JSON artifact: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def build_snapshot() -> dict:
    snapshot_timestamp = datetime.now(UTC).isoformat()

    manifest = load_json(MANIFEST_PATH)
    governance = load_json(GOVERNANCE_PATH)

    snapshot = {
        "snapshot_timestamp_utc": snapshot_timestamp,
        "environment": config["environment"],
        "runtime_directory": str(RUNTIME_DIR),
        "source_artifacts": {
            "manifest": str(MANIFEST_PATH),
            "governance": str(GOVERNANCE_PATH),
            "checkpoint_summary": str(CHECKPOINT_PATH),
            "health_summary": str(HEALTH_PATH),
        },
        "system_status": manifest.get("system_status", {}),
        "governance_decision": governance,
    }

    logger.info(
        "Runtime state snapshot built | decision=%s | approved=%s | runtime_stable=%s",
        governance.get("decision"),
        governance.get("approved"),
        manifest.get("system_status", {}).get("runtime_stable"),
    )

    return snapshot


def write_snapshot(snapshot: dict) -> Path:
    timestamp_safe = snapshot["snapshot_timestamp_utc"].replace(":", "-")
    snapshot_path = STATE_DIR / f"runtime_state_{timestamp_safe}.json"

    snapshot_path.write_text(
        json.dumps(snapshot, indent=2),
        encoding="utf-8",
    )

    LATEST_SNAPSHOT_PATH.write_text(
        json.dumps(snapshot, indent=2),
        encoding="utf-8",
    )

    with REGISTRY_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(snapshot) + "\n")

    logger.info("Saved timestamped runtime state snapshot: %s", snapshot_path)
    logger.info("Updated latest runtime state snapshot: %s", LATEST_SNAPSHOT_PATH)
    logger.info("Appended runtime state registry: %s", REGISTRY_PATH)

    return snapshot_path


def main():
    logger.info("=" * 90)
    logger.info("AURUM RUNTIME STATE SNAPSHOT ENGINE")
    logger.info("=" * 90)

    snapshot = build_snapshot()
    snapshot_path = write_snapshot(snapshot)

    logger.info("Runtime state snapshot completed successfully: %s", snapshot_path)


if __name__ == "__main__":
    main()