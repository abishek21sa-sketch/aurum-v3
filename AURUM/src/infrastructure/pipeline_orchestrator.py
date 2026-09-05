from datetime import datetime, timezone
import subprocess
import sys
import uuid

from src.infrastructure.pipeline_runtime import (
    append_pipeline_record,
    save_failure_trace,
)
from src.infrastructure.logger import get_logger


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_pipeline_step(
    run_id: str,
    pipeline_name: str,
    step_name: str,
    module_name: str,
    logger,
) -> bool:
    started_at = datetime.now(timezone.utc)

    print("\n" + "=" * 80)
    print(f"RUNNING STEP: {step_name}")
    print(f"MODULE: {module_name}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", module_name],
            check=True,
            capture_output=True,
            text=True,
        )

        if result.stdout:
            print(result.stdout)
            logger.info(result.stdout.strip())

        finished_at = datetime.now(timezone.utc)
        duration = (finished_at - started_at).total_seconds()

        append_pipeline_record(
            {
                "run_id": run_id,
                "pipeline_name": pipeline_name,
                "step_name": step_name,
                "module_name": module_name,
                "status": "success",
                "started_at_utc": started_at.isoformat(),
                "finished_at_utc": finished_at.isoformat(),
                "duration_seconds": duration,
                "error_message": "",
            }
        )

        print(f"STEP PASSED: {step_name}")
        return True

    except subprocess.CalledProcessError as error:
        finished_at = datetime.now(timezone.utc)
        duration = (finished_at - started_at).total_seconds()

        if error.stdout:
            print(error.stdout)
            logger.error(error.stdout.strip())

        if error.stderr:
            print(error.stderr)
            logger.error(error.stderr.strip())

        failure_path = save_failure_trace(run_id, step_name, error)

        append_pipeline_record(
            {
                "run_id": run_id,
                "pipeline_name": pipeline_name,
                "step_name": step_name,
                "module_name": module_name,
                "status": "failed",
                "started_at_utc": started_at.isoformat(),
                "finished_at_utc": finished_at.isoformat(),
                "duration_seconds": duration,
                "error_message": str(error),
            }
        )

        print(f"STEP FAILED: {step_name}")
        print(f"Failure trace: {failure_path}")
        return False


def run_pipeline(
    pipeline_name: str,
    steps: list[dict],
    fail_fast: bool = True,
) -> str:
    run_id = f"{pipeline_name}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"

    logger = get_logger(
        logger_name=f"aurum.pipeline.{pipeline_name}",
        log_filename=f"{run_id}.log",
    )

    logger.info(f"Starting pipeline: {pipeline_name}")
    logger.info(f"Run ID: {run_id}")

    print("\n" + "#" * 80)
    print(f"STARTING PIPELINE: {pipeline_name}")
    print(f"RUN ID: {run_id}")
    print("#" * 80)

    failed_steps = []

    for step in steps:

        logger.info(f"Starting step: {step['step_name']} | Module: {step['module_name']}")
        success = run_pipeline_step(
            run_id=run_id,
            pipeline_name=pipeline_name,
            step_name=step["step_name"],
            module_name=step["module_name"],
            logger=logger,
        )

        if success:
            logger.info(f"Step passed: {step['step_name']}")
        else:
            logger.error(f"Step failed: {step['step_name']}")

        if not success:
            failed_steps.append(step["step_name"])
            if fail_fast:
                break

    print("\n" + "#" * 80)
    print(f"PIPELINE COMPLETE: {pipeline_name}")
    print(f"RUN ID: {run_id}")

    if failed_steps:
        logger.error(f"Pipeline completed with failures: {failed_steps}")
    else:
        logger.info("Pipeline completed successfully")

    print("#" * 80)

    return run_id


if __name__ == "__main__":
    test_steps = [
        {
            "step_name": "storage_validation",
            "module_name": "src.infrastructure.validate_storage_layer",
        },
        {
            "step_name": "runtime_environment_summary",
            "module_name": "src.infrastructure.runtime_environment",
        },
    ]

    run_pipeline(
        pipeline_name="infrastructure_smoke_test",
        steps=test_steps,
        fail_fast=True,
    )
