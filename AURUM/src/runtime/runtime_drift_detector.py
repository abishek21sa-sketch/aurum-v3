# src/runtime/runtime_drift_detector.py

import json
from pathlib import Path

import pandas as pd

from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("runtime.drift_detector")


RUNTIME_DIR = Path(config["runtime"]["output_dir"])
STATE_DIR = RUNTIME_DIR / "state"

REGISTRY_PATH = STATE_DIR / "runtime_state_registry.jsonl"

OUTPUT_JSON = RUNTIME_DIR / "runtime_drift_report.json"
OUTPUT_TXT = RUNTIME_DIR / "runtime_drift_report.txt"


def load_state_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        logger.error("Runtime state registry not found: %s", REGISTRY_PATH)
        raise FileNotFoundError(f"Runtime state registry not found: {REGISTRY_PATH}")

    records = []

    with REGISTRY_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    logger.info("Loaded %s runtime state snapshots.", len(records))

    return records


def build_registry_frame(records: list[dict]) -> pd.DataFrame:
    rows = []

    for record in records:
        system_status = record.get("system_status", {})
        governance = record.get("governance_decision", {})
        metrics = governance.get("metrics", {})

        rows.append(
            {
                "snapshot_timestamp_utc": record.get("snapshot_timestamp_utc"),
                "environment": record.get("environment"),
                "decision": governance.get("decision"),
                "severity": governance.get("severity"),
                "approved": governance.get("approved"),
                "pass_rate": system_status.get("pass_rate"),
                "total_runtime_seconds": system_status.get("total_runtime_seconds"),
                "runtime_stable": system_status.get("runtime_stable"),
                "failed_modules": metrics.get("failed_modules"),
                "stderr_modules": metrics.get("stderr_modules"),
                "failed_checkpoints": metrics.get("failed_checkpoints"),
            }
        )

    df = pd.DataFrame(rows)

    if not df.empty:
        df["snapshot_timestamp_utc"] = pd.to_datetime(
            df["snapshot_timestamp_utc"],
            errors="coerce",
        )
        df = df.sort_values("snapshot_timestamp_utc").reset_index(drop=True)

    logger.info("Built runtime registry frame with %s rows.", len(df))

    return df


def detect_drift(df: pd.DataFrame) -> dict:
    if len(df) < 2:
        logger.warning("Not enough runtime snapshots for drift detection.")
        return {
            "drift_detected": False,
            "severity": "INSUFFICIENT_HISTORY",
            "reason": "At least two runtime snapshots are required for drift detection.",
            "current_state": df.iloc[-1].to_dict() if not df.empty else {},
            "previous_state": {},
            "drift_signals": {},
        }

    previous = df.iloc[-2]
    current = df.iloc[-1]

    drift_signals = {
        "governance_decision_changed": previous["decision"] != current["decision"],
        "severity_changed": previous["severity"] != current["severity"],
        "approval_status_changed": bool(previous["approved"]) != bool(current["approved"]),
        "pass_rate_declined": float(current["pass_rate"]) < float(previous["pass_rate"]),
        "runtime_duration_increased": float(current["total_runtime_seconds"])
        > float(previous["total_runtime_seconds"]),
        "runtime_stability_degraded": bool(previous["runtime_stable"])
        and not bool(current["runtime_stable"]),
        "failed_modules_increased": int(current["failed_modules"])
        > int(previous["failed_modules"]),
        "stderr_modules_increased": int(current["stderr_modules"])
        > int(previous["stderr_modules"]),
        "failed_checkpoints_increased": int(current["failed_checkpoints"])
        > int(previous["failed_checkpoints"]),
    }

    drift_detected = any(drift_signals.values())

    critical_signals = [
        "governance_decision_changed",
        "approval_status_changed",
        "runtime_stability_degraded",
        "failed_modules_increased",
        "failed_checkpoints_increased",
    ]

    warning_signals = [
        "severity_changed",
        "pass_rate_declined",
        "runtime_duration_increased",
        "stderr_modules_increased",
    ]

    if any(drift_signals[key] for key in critical_signals):
        severity = "CRITICAL"
    elif any(drift_signals[key] for key in warning_signals):
        severity = "WARNING"
    else:
        severity = "STABLE"

    logger.info(
        "Runtime drift evaluated | drift_detected=%s | severity=%s",
        drift_detected,
        severity,
    )

    return {
        "drift_detected": drift_detected,
        "severity": severity,
        "previous_state": previous.to_dict(),
        "current_state": current.to_dict(),
        "drift_signals": drift_signals,
    }


def make_json_safe(value):
    if pd.isna(value):
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()

    return value


def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {key: sanitize_for_json(value) for key, value in obj.items()}

    if isinstance(obj, list):
        return [sanitize_for_json(value) for value in obj]

    return make_json_safe(obj)


def write_text_report(report: dict) -> None:
    lines = [
        "=" * 90,
        "AURUM RUNTIME DRIFT DETECTOR",
        "=" * 90,
        "",
        "DRIFT SUMMARY",
        "-" * 70,
        f"Drift Detected: {report['drift_detected']}",
        f"Severity: {report['severity']}",
        "",
        "DRIFT SIGNALS",
        "-" * 70,
    ]

    for signal, detected in report["drift_signals"].items():
        status = "TRIGGERED" if detected else "clear"
        lines.append(f"{signal}: {status}")

    current = report.get("current_state", {})
    previous = report.get("previous_state", {})

    lines.extend(
        [
            "",
            "PREVIOUS STATE",
            "-" * 70,
        ]
    )

    if previous:
        for key, value in previous.items():
            lines.append(f"{key}: {value}")
    else:
        lines.append("No previous state available.")

    lines.extend(
        [
            "",
            "CURRENT STATE",
            "-" * 70,
        ]
    )

    if current:
        for key, value in current.items():
            lines.append(f"{key}: {value}")
    else:
        lines.append("No current state available.")

    lines.extend(
        [
            "",
            "INSTITUTIONAL INTERPRETATION",
            "-" * 70,
        ]
    )

    if report["severity"] == "STABLE":
        lines.append("Runtime behavior is stable relative to the previous snapshot.")
    elif report["severity"] == "WARNING":
        lines.append(
            "Runtime drift warning detected. Review duration, stderr, or pass-rate changes."
        )
    elif report["severity"] == "CRITICAL":
        lines.append(
            "Critical runtime drift detected. Governance, stability, failures, or checkpoints changed materially."
        )
    else:
        lines.append("Insufficient runtime history for drift evaluation.")

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")

    logger.info("Saved runtime drift text report: %s", OUTPUT_TXT)


def main():
    logger.info("=" * 90)
    logger.info("AURUM RUNTIME DRIFT DETECTOR")
    logger.info("=" * 90)

    records = load_state_registry()
    df = build_registry_frame(records)
    report = detect_drift(df)

    safe_report = sanitize_for_json(report)

    OUTPUT_JSON.write_text(
        json.dumps(safe_report, indent=2),
        encoding="utf-8",
    )

    logger.info("Saved runtime drift JSON report: %s", OUTPUT_JSON)

    write_text_report(safe_report)

    logger.info("Runtime drift detector completed successfully.")


if __name__ == "__main__":
    main()