# src/runtime/runtime_health_monitor.py

from pathlib import Path

import pandas as pd

from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("runtime.health_monitor")


RUNTIME_DIR = Path(config["runtime"]["output_dir"])

SUMMARY_PATH = RUNTIME_DIR / "runtime_health_summary.csv"
REPORT_PATH = RUNTIME_DIR / "runtime_health_report.txt"


def parse_log_file(log_path: Path, execution_order: int) -> dict:
    text = log_path.read_text(encoding="utf-8", errors="ignore")

    module_name = "unknown"
    status = "UNKNOWN"
    start = None
    end = None

    for line in text.splitlines():
        if line.startswith("MODULE:"):
            module_name = line.replace("MODULE:", "").strip()
        elif line.startswith("STATUS:"):
            status = line.replace("STATUS:", "").strip()
        elif line.startswith("START:"):
            start = line.replace("START:", "").strip()
        elif line.startswith("END:"):
            end = line.replace("END:", "").strip()

    runtime_seconds = None

    if start and end:
        try:
            runtime_seconds = (
                pd.to_datetime(end) - pd.to_datetime(start)
            ).total_seconds()
        except Exception:
            runtime_seconds = None

    stderr_present = (
        "STDERR:" in text
        and len(text.split("STDERR:", 1)[-1].strip()) > 0
    )

    logger.info(
        "Parsed runtime log | module=%s | status=%s | runtime_seconds=%s | stderr=%s",
        module_name,
        status,
        runtime_seconds,
        stderr_present,
    )

    return {
        "execution_order": execution_order,
        "module_name": module_name,
        "status": status,
        "runtime_seconds": runtime_seconds,
        "log_size_kb": round(log_path.stat().st_size / 1024, 3),
        "failure_detected": status != "PASS",
        "stderr_present": stderr_present,
        "log_path": str(log_path),
    }


def get_orchestrated_module_order() -> list[str]:
    orchestration_summary_path = (
        RUNTIME_DIR / "runtime_orchestration_summary.txt"
    )

    if not orchestration_summary_path.exists():
        logger.warning(
            "runtime_orchestration_summary.txt not found. Falling back to log sorting."
        )
        return []

    modules = []

    for line in orchestration_summary_path.read_text(
        encoding="utf-8"
    ).splitlines():
        if " | " in line and line.startswith("src."):
            module_name = line.split(" | ")[0].strip()
            modules.append(module_name)

    logger.info(
        "Loaded orchestrated module order for %s modules.",
        len(modules),
    )

    return modules


def build_health_summary() -> pd.DataFrame:
    module_order = get_orchestrated_module_order()

    records = []

    if module_order:
        for idx, module_name in enumerate(module_order):
            log_path = (
                RUNTIME_DIR / f"{module_name.replace('.', '_')}.log"
            )

            if log_path.exists():
                records.append(parse_log_file(log_path, idx + 1))
            else:
                logger.warning(
                    "Expected runtime log missing: %s",
                    log_path,
                )
    else:
        fallback_logs = sorted(RUNTIME_DIR.glob("*.log"))

        logger.warning(
            "Using fallback alphabetical log ordering for %s logs.",
            len(fallback_logs),
        )

        for idx, log_path in enumerate(fallback_logs):
            records.append(parse_log_file(log_path, idx + 1))

    df = pd.DataFrame(records)

    logger.info(
        "Built runtime health summary | total_modules=%s",
        len(df),
    )

    return df


def write_health_report(df: pd.DataFrame) -> None:
    total_modules = len(df)
    passed_modules = int((df["status"] == "PASS").sum())
    failed_modules = int((df["status"] != "PASS").sum())
    stderr_modules = int(df["stderr_present"].sum())

    pass_rate = (
        passed_modules / total_modules
        if total_modules
        else 0.0
    )

    slowest = df.sort_values(
        "runtime_seconds",
        ascending=False,
    ).head(3)

    logger.info(
        "Runtime health metrics | total=%s | passed=%s | failed=%s | stderr=%s | pass_rate=%.4f",
        total_modules,
        passed_modules,
        failed_modules,
        stderr_modules,
        pass_rate,
    )

    lines = [
        "=" * 90,
        "AURUM RUNTIME HEALTH MONITOR",
        "=" * 90,
        "",
        "SYSTEM HEALTH SUMMARY",
        "-" * 70,
        f"Total Modules Executed: {total_modules}",
        f"Passed Modules: {passed_modules}",
        f"Failed Modules: {failed_modules}",
        f"Pass Rate: {pass_rate:.2%}",
        f"Modules With STDERR: {stderr_modules}",
        "",
        "SLOWEST MODULES",
        "-" * 70,
    ]

    for _, row in slowest.iterrows():
        lines.append(
            f"{row['module_name']} | "
            f"{row['runtime_seconds']:.4f}s | "
            f"{row['status']}"
        )

    lines.extend(
        [
            "",
            "MODULE HEALTH TABLE",
            "-" * 70,
        ]
    )

    for _, row in df.iterrows():
        lines.append(
            f"{row['execution_order']:02d}. "
            f"{row['module_name']} | "
            f"{row['status']} | "
            f"runtime={row['runtime_seconds']:.4f}s | "
            f"stderr={row['stderr_present']} | "
            f"log_size_kb={row['log_size_kb']}"
        )

    if failed_modules == 0:
        interpretation = (
            "Runtime health is stable. "
            "All orchestrated modules completed successfully."
        )
    else:
        interpretation = (
            "Runtime health is degraded. "
            "One or more modules failed and require investigation."
        )

    lines.extend(
        [
            "",
            "INSTITUTIONAL INTERPRETATION",
            "-" * 70,
            interpretation,
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    logger.info("Saved runtime health report: %s", REPORT_PATH)


def main():
    logger.info("=" * 90)
    logger.info("AURUM RUNTIME HEALTH MONITOR")
    logger.info("=" * 90)

    df = build_health_summary()

    if df.empty:
        logger.error(
            "No runtime logs found. Run the orchestrator first."
        )
        return

    df.to_csv(SUMMARY_PATH, index=False)

    logger.info(
        "Saved runtime health summary: %s",
        SUMMARY_PATH,
    )

    write_health_report(df)

    logger.info(
        "Runtime health monitor completed successfully."
    )


if __name__ == "__main__":
    main()