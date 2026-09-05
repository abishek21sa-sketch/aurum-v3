# src/runtime/runtime_checkpoint_engine.py

from pathlib import Path
from datetime import datetime, UTC

import pandas as pd

from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("runtime.checkpoint_engine")


RUNTIME_DIR = Path(config["runtime"]["output_dir"])

CHECKPOINT_OUTPUTS = config["checkpoints"]["required_outputs"]

OUTPUT_CSV = RUNTIME_DIR / "runtime_checkpoint_summary.csv"
OUTPUT_REPORT = RUNTIME_DIR / "runtime_checkpoint_report.txt"


def inspect_artifact(path_str: str) -> dict:
    path = Path(path_str)

    exists = path.exists()
    size_kb = round(path.stat().st_size / 1024, 3) if exists else 0.0
    modified_utc = (
        datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
        if exists
        else None
    )

    checkpoint_passed = exists and size_kb > 0

    if checkpoint_passed:
        logger.info("Checkpoint PASS | %s | size_kb=%s", path_str, size_kb)
    else:
        logger.warning("Checkpoint FAIL | %s | exists=%s | size_kb=%s", path_str, exists, size_kb)

    return {
        "artifact_path": path_str,
        "exists": exists,
        "size_kb": size_kb,
        "modified_utc": modified_utc,
        "checkpoint_passed": checkpoint_passed,
    }


def build_checkpoint_summary() -> pd.DataFrame:
    logger.info("Building checkpoint summary for %s required artifacts.", len(CHECKPOINT_OUTPUTS))

    records = [inspect_artifact(path) for path in CHECKPOINT_OUTPUTS]
    return pd.DataFrame(records)


def write_checkpoint_report(df: pd.DataFrame) -> None:
    total = len(df)
    passed = int(df["checkpoint_passed"].sum())
    failed = total - passed
    pass_rate = passed / total if total else 0.0

    logger.info(
        "Checkpoint report metrics | total=%s | passed=%s | failed=%s | pass_rate=%.2f",
        total,
        passed,
        failed,
        pass_rate,
    )

    lines = [
        "=" * 90,
        "AURUM RUNTIME CHECKPOINT ENGINE",
        "=" * 90,
        "",
        "CHECKPOINT SUMMARY",
        "-" * 70,
        f"Total Required Artifacts: {total}",
        f"Artifacts Present And Non-Empty: {passed}",
        f"Artifacts Missing Or Empty: {failed}",
        f"Checkpoint Pass Rate: {pass_rate:.2%}",
        "",
        "ARTIFACT CHECKPOINT TABLE",
        "-" * 70,
    ]

    for _, row in df.iterrows():
        status = "PASS" if row["checkpoint_passed"] else "FAIL"
        lines.append(
            f"{status} | {row['artifact_path']} | "
            f"exists={row['exists']} | size_kb={row['size_kb']} | "
            f"modified_utc={row['modified_utc']}"
        )

    if failed == 0:
        interpretation = (
            "All required runtime artifacts are present and non-empty. "
            "AURUM checkpoint integrity is stable."
        )
    else:
        interpretation = (
            "One or more required runtime artifacts are missing or empty. "
            "AURUM checkpoint integrity requires review."
        )

    lines.extend(
        [
            "",
            "INSTITUTIONAL INTERPRETATION",
            "-" * 70,
            interpretation,
        ]
    )

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")

    logger.info("Saved checkpoint report: %s", OUTPUT_REPORT)


def main():
    logger.info("=" * 90)
    logger.info("AURUM RUNTIME CHECKPOINT ENGINE")
    logger.info("=" * 90)

    df = build_checkpoint_summary()

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    logger.info("Saved checkpoint summary: %s", OUTPUT_CSV)

    write_checkpoint_report(df)

    logger.info("Checkpoint engine completed successfully.")


if __name__ == "__main__":
    main()