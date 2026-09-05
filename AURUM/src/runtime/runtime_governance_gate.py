# src/runtime/runtime_governance_gate.py

import json
from pathlib import Path

import pandas as pd

from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("runtime.governance_gate")


RUNTIME_DIR = Path(config["runtime"]["output_dir"])

MANIFEST_PATH = RUNTIME_DIR / "runtime_manifest.json"
HEALTH_SUMMARY_PATH = RUNTIME_DIR / "runtime_health_summary.csv"
CHECKPOINT_SUMMARY_PATH = RUNTIME_DIR / "runtime_checkpoint_summary.csv"

OUTPUT_JSON = RUNTIME_DIR / "runtime_governance_decision.json"
OUTPUT_TXT = RUNTIME_DIR / "runtime_governance_decision.txt"

MIN_PASS_RATE = config["governance"]["min_pass_rate"]
ALLOW_STDERR = config["governance"]["allow_stderr"]
REQUIRE_ALL_CHECKPOINTS = config["governance"]["require_all_checkpoints"]


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        logger.error("runtime_manifest.json not found.")
        raise FileNotFoundError("runtime_manifest.json not found.")

    logger.info("Loaded runtime manifest.")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_health_summary() -> pd.DataFrame:
    if not HEALTH_SUMMARY_PATH.exists():
        logger.error("runtime_health_summary.csv not found.")
        raise FileNotFoundError("runtime_health_summary.csv not found.")

    logger.info("Loaded runtime health summary.")
    return pd.read_csv(HEALTH_SUMMARY_PATH)


def load_checkpoint_summary() -> pd.DataFrame:
    if not CHECKPOINT_SUMMARY_PATH.exists():
        logger.error("runtime_checkpoint_summary.csv not found.")
        raise FileNotFoundError("runtime_checkpoint_summary.csv not found.")

    logger.info("Loaded runtime checkpoint summary.")
    return pd.read_csv(CHECKPOINT_SUMMARY_PATH)


def evaluate_governance(
    manifest: dict,
    health_df: pd.DataFrame,
    checkpoint_df: pd.DataFrame,
) -> dict:
    system_status = manifest["system_status"]

    runtime_stable = bool(system_status["runtime_stable"])
    pass_rate = float(system_status["pass_rate"])
    failed_modules = int(system_status["failed_modules"])

    stderr_modules = int(health_df["stderr_present"].sum())
    failed_checkpoints = int((~checkpoint_df["checkpoint_passed"]).sum())

    conditions = {
        "runtime_stable": runtime_stable,
        "pass_rate_requirement_met": pass_rate >= MIN_PASS_RATE,
        "no_failed_modules": failed_modules == 0,
        "stderr_requirement_met": stderr_modules == 0 if not ALLOW_STDERR else True,
        "checkpoint_requirement_met": failed_checkpoints == 0
        if REQUIRE_ALL_CHECKPOINTS
        else True,
    }

    approved = all(conditions.values())

    if approved:
        decision = "ACCEPT_RUN"
        severity = "GREEN"
        action = "Proceed to institutional live-mode readiness."
    elif runtime_stable and failed_checkpoints > 0:
        decision = "QUARANTINE_RUN"
        severity = "YELLOW"
        action = "Runtime passed, but artifact integrity failed. Review missing outputs."
    else:
        decision = "ESCALATE_RUN"
        severity = "RED"
        action = "Runtime is unstable. Investigate failed modules or stderr immediately."

    logger.info(
        "Governance evaluated | decision=%s | severity=%s | approved=%s | "
        "pass_rate=%.4f | failed_modules=%s | stderr_modules=%s | failed_checkpoints=%s",
        decision,
        severity,
        approved,
        pass_rate,
        failed_modules,
        stderr_modules,
        failed_checkpoints,
    )

    return {
        "decision": decision,
        "severity": severity,
        "approved": approved,
        "action": action,
        "conditions": conditions,
        "metrics": {
            "pass_rate": pass_rate,
            "failed_modules": failed_modules,
            "stderr_modules": stderr_modules,
            "failed_checkpoints": failed_checkpoints,
        },
    }


def write_text_report(governance: dict) -> None:
    lines = [
        "=" * 90,
        "AURUM RUNTIME GOVERNANCE GATE",
        "=" * 90,
        "",
        "GOVERNANCE DECISION",
        "-" * 70,
        f"Decision: {governance['decision']}",
        f"Severity: {governance['severity']}",
        f"Approved: {governance['approved']}",
        f"Recommended Action: {governance['action']}",
        "",
        "GOVERNANCE CONDITIONS",
        "-" * 70,
    ]

    for condition, passed in governance["conditions"].items():
        status = "PASS" if passed else "FAIL"
        lines.append(f"{condition}: {status}")

    lines.extend(
        [
            "",
            "GOVERNANCE METRICS",
            "-" * 70,
        ]
    )

    for metric, value in governance["metrics"].items():
        lines.append(f"{metric}: {value}")

    lines.extend(
        [
            "",
            "INSTITUTIONAL INTERPRETATION",
            "-" * 70,
        ]
    )

    if governance["approved"]:
        lines.append(
            "This run satisfies the runtime stability, health, and checkpoint requirements."
        )
    else:
        lines.append(
            "This run does not satisfy all institutional governance requirements."
        )

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved governance text report: %s", OUTPUT_TXT)


def main():
    logger.info("=" * 90)
    logger.info("AURUM RUNTIME GOVERNANCE GATE")
    logger.info("=" * 90)

    manifest = load_manifest()
    health_df = load_health_summary()
    checkpoint_df = load_checkpoint_summary()

    governance = evaluate_governance(manifest, health_df, checkpoint_df)

    OUTPUT_JSON.write_text(json.dumps(governance, indent=2), encoding="utf-8")
    logger.info("Saved governance JSON: %s", OUTPUT_JSON)

    write_text_report(governance)

    logger.info("Decision: %s", governance["decision"])
    logger.info("Severity: %s", governance["severity"])
    logger.info("Approved: %s", governance["approved"])


if __name__ == "__main__":
    main()