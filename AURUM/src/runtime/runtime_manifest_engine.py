# src/runtime/runtime_manifest_engine.py

import json
import platform
import sys
from datetime import datetime, UTC
from pathlib import Path

import pandas as pd

from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("runtime.manifest_engine")


RUNTIME_DIR = Path(config["runtime"]["output_dir"])

HEALTH_SUMMARY_PATH = RUNTIME_DIR / "runtime_health_summary.csv"
MANIFEST_JSON_PATH = RUNTIME_DIR / "runtime_manifest.json"
MANIFEST_TXT_PATH = RUNTIME_DIR / "runtime_manifest.txt"


def load_health_summary() -> pd.DataFrame:
    if not HEALTH_SUMMARY_PATH.exists():
        logger.error("runtime_health_summary.csv not found.")
        raise FileNotFoundError(
            "runtime_health_summary.csv not found. Run runtime_health_monitor first."
        )

    logger.info("Loaded runtime health summary: %s", HEALTH_SUMMARY_PATH)
    return pd.read_csv(HEALTH_SUMMARY_PATH)


def build_manifest(df: pd.DataFrame) -> dict:
    total_modules = len(df)
    passed_modules = int((df["status"] == "PASS").sum())
    failed_modules = int((df["status"] != "PASS").sum())

    total_runtime_seconds = float(df["runtime_seconds"].sum())
    pass_rate = passed_modules / total_modules if total_modules else 0.0

    manifest = {
        "run_metadata": {
            "run_timestamp_utc": datetime.now(UTC).isoformat(),
            "platform": platform.platform(),
            "python_version": sys.version,
            "runtime_directory": str(RUNTIME_DIR),
            "environment": config["environment"],
        },
        "system_status": {
            "total_modules": total_modules,
            "passed_modules": passed_modules,
            "failed_modules": failed_modules,
            "pass_rate": pass_rate,
            "total_runtime_seconds": total_runtime_seconds,
            "runtime_stable": failed_modules == 0,
        },
        "module_results": df.to_dict(orient="records"),
    }

    logger.info(
        "Manifest built | total_modules=%s | passed=%s | failed=%s | pass_rate=%.4f | runtime_stable=%s",
        total_modules,
        passed_modules,
        failed_modules,
        pass_rate,
        failed_modules == 0,
    )

    return manifest


def write_manifest_text(manifest: dict) -> None:
    metadata = manifest["run_metadata"]
    status = manifest["system_status"]
    modules = manifest["module_results"]

    lines = [
        "=" * 90,
        "AURUM RUNTIME MANIFEST",
        "=" * 90,
        "",
        "RUN METADATA",
        "-" * 70,
        f"Run Timestamp UTC: {metadata['run_timestamp_utc']}",
        f"Environment: {metadata['environment']}",
        f"Platform: {metadata['platform']}",
        f"Python Version: {metadata['python_version'].split()[0]}",
        f"Runtime Directory: {metadata['runtime_directory']}",
        "",
        "SYSTEM STATUS",
        "-" * 70,
        f"Total Modules: {status['total_modules']}",
        f"Passed Modules: {status['passed_modules']}",
        f"Failed Modules: {status['failed_modules']}",
        f"Pass Rate: {status['pass_rate']:.2%}",
        f"Total Runtime Seconds: {status['total_runtime_seconds']:.4f}",
        f"Runtime Stable: {status['runtime_stable']}",
        "",
        "MODULE RESULTS",
        "-" * 70,
    ]

    for module in modules:
        lines.append(
            f"{int(module['execution_order']):02d}. "
            f"{module['module_name']} | "
            f"{module['status']} | "
            f"{float(module['runtime_seconds']):.4f}s | "
            f"stderr={module['stderr_present']}"
        )

    if status["runtime_stable"]:
        interpretation = (
            "AURUM runtime execution is institutionally stable for this run."
        )
    else:
        interpretation = (
            "AURUM runtime execution is not stable. Failed modules require review."
        )

    lines.extend(
        [
            "",
            "INSTITUTIONAL INTERPRETATION",
            "-" * 70,
            interpretation,
        ]
    )

    MANIFEST_TXT_PATH.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved manifest text report: %s", MANIFEST_TXT_PATH)


def main():
    logger.info("=" * 90)
    logger.info("AURUM RUNTIME MANIFEST ENGINE")
    logger.info("=" * 90)

    df = load_health_summary()
    manifest = build_manifest(df)

    MANIFEST_JSON_PATH.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    logger.info("Saved manifest JSON: %s", MANIFEST_JSON_PATH)

    write_manifest_text(manifest)

    logger.info("Runtime manifest engine completed successfully.")


if __name__ == "__main__":
    main()