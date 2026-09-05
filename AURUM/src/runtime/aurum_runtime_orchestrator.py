# src/runtime/aurum_runtime_orchestrator.py

import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path

from src.config.config_loader import load_config
from src.logging.runtime_logger import get_logger


config = load_config()
logger = get_logger("runtime.orchestrator")


PIPELINE_STEPS = [
    "src.optimization.market_regime_detector",
    "src.regimes.regime_transition_engine",
    "src.regimes.regime_forecast_engine",
    "src.optimization.probabilistic_regime_allocator",
    "src.risk.live_scenario_shock_engine",
    "src.ai.recursive_self_evaluation_engine",
]


RUNTIME_DIR = Path(config["runtime"]["output_dir"])
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

HALT_ON_FAILURE = config["runtime"].get("halt_on_failure", True)
MAX_RETRIES = config["runtime"].get("max_retries", 2)
RETRY_DELAY_SECONDS = config["runtime"].get("retry_delay_seconds", 3)


def execute_module_once(module_name: str, attempt: int) -> dict:
    logger.info("=" * 90)
    logger.info("RUNNING: %s | attempt=%s", module_name, attempt)
    logger.info("=" * 90)

    start = datetime.now(UTC)

    result = subprocess.run(
        [sys.executable, "-m", module_name],
        capture_output=True,
        text=True,
    )

    end = datetime.now(UTC)
    runtime_seconds = (end - start).total_seconds()
    status = "PASS" if result.returncode == 0 else "FAIL"

    if result.stdout:
        logger.info("STDOUT for %s:\n%s", module_name, result.stdout.strip())

    if result.stderr:
        logger.warning("STDERR for %s:\n%s", module_name, result.stderr.strip())

    logger.info(
        "Module attempt completed | module=%s | attempt=%s | status=%s | return_code=%s | runtime_seconds=%.4f",
        module_name,
        attempt,
        status,
        result.returncode,
        runtime_seconds,
    )

    return {
        "module": module_name,
        "attempt": attempt,
        "status": status,
        "return_code": result.returncode,
        "runtime_seconds": runtime_seconds,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "start": start,
        "end": end,
    }


def write_step_log(module_name: str, attempts: list[dict], final_result: dict) -> Path:
    log_path = RUNTIME_DIR / f"{module_name.replace('.', '_')}.log"

    lines = [
        f"MODULE: {module_name}",
        f"STATUS: {final_result['status']}",
        f"START: {attempts[0]['start']}",
        f"END: {final_result['end']}",
        f"RETURN CODE: {final_result['return_code']}",
        f"RUNTIME_SECONDS: {sum(item['runtime_seconds'] for item in attempts):.6f}",
        f"ATTEMPTS: {len(attempts)}",
        "",
        "ATTEMPT SUMMARY:",
    ]

    for item in attempts:
        lines.append(
            f"attempt={item['attempt']} | "
            f"status={item['status']} | "
            f"return_code={item['return_code']} | "
            f"runtime_seconds={item['runtime_seconds']:.6f}"
        )

    lines.extend(["", "STDOUT:"])
    lines.append(final_result["stdout"])

    lines.extend(["", "STDERR:"])
    lines.append(final_result["stderr"])

    log_path.write_text("\n".join(lines), encoding="utf-8")

    logger.info("Saved module runtime log: %s", log_path)

    return log_path


def run_step(module_name: str) -> dict:
    attempts = []

    total_allowed_attempts = MAX_RETRIES + 1

    for attempt in range(1, total_allowed_attempts + 1):
        result = execute_module_once(module_name, attempt)
        attempts.append(result)

        if result["status"] == "PASS":
            log_path = write_step_log(module_name, attempts, result)

            return {
                "module": module_name,
                "status": result["status"],
                "return_code": result["return_code"],
                "runtime_seconds": sum(item["runtime_seconds"] for item in attempts),
                "attempts": len(attempts),
                "log_path": str(log_path),
                "start": attempts[0]["start"].isoformat(),
                "end": result["end"].isoformat(),
            }

        if attempt < total_allowed_attempts:
            logger.warning(
                "Module failed. Retrying | module=%s | attempt=%s/%s | retry_delay_seconds=%s",
                module_name,
                attempt,
                total_allowed_attempts,
                RETRY_DELAY_SECONDS,
            )
            time.sleep(RETRY_DELAY_SECONDS)

    final_result = attempts[-1]
    log_path = write_step_log(module_name, attempts, final_result)

    logger.error(
        "Module failed after all retry attempts | module=%s | attempts=%s",
        module_name,
        len(attempts),
    )

    return {
        "module": module_name,
        "status": final_result["status"],
        "return_code": final_result["return_code"],
        "runtime_seconds": sum(item["runtime_seconds"] for item in attempts),
        "attempts": len(attempts),
        "log_path": str(log_path),
        "start": attempts[0]["start"].isoformat(),
        "end": final_result["end"].isoformat(),
    }


def write_orchestration_summary(summary: list[dict]) -> Path:
    summary_path = RUNTIME_DIR / "runtime_orchestration_summary.txt"

    lines = [
        "AURUM PHASE 2C RUNTIME ORCHESTRATION SUMMARY",
        "=" * 90,
    ]

    for item in summary:
        lines.append(
            f"{item['module']} | "
            f"{item['status']} | "
            f"return_code={item['return_code']} | "
            f"attempts={item['attempts']} | "
            f"runtime_seconds={item['runtime_seconds']:.4f} | "
            f"log={item['log_path']}"
        )

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    logger.info("Saved orchestration summary: %s", summary_path)

    return summary_path


def main():
    logger.info("=" * 90)
    logger.info("AURUM PHASE 2C RUNTIME ORCHESTRATOR WITH RETRY RECOVERY")
    logger.info("=" * 90)

    summary = []

    for step in PIPELINE_STEPS:
        result = run_step(step)
        summary.append(result)

        if result["status"] == "FAIL" and HALT_ON_FAILURE:
            logger.error("Runtime halted due to failed module: %s", step)
            break

    write_orchestration_summary(summary)

    passed = sum(1 for item in summary if item["status"] == "PASS")
    failed = sum(1 for item in summary if item["status"] == "FAIL")
    total_attempts = sum(item["attempts"] for item in summary)

    logger.info("=" * 90)
    logger.info("RUNTIME ORCHESTRATION SUMMARY")
    logger.info("=" * 90)

    for item in summary:
        logger.info(
            "%s | %s | attempts=%s",
            item["module"],
            item["status"],
            item["attempts"],
        )

    logger.info(
        "Runtime orchestration completed | passed=%s | failed=%s | total_modules=%s | total_attempts=%s",
        passed,
        failed,
        len(summary),
        total_attempts,
    )


if __name__ == "__main__":
    main()