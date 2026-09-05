from datetime import datetime, timezone
from pathlib import Path
import traceback
import json
import pandas as pd

from src.infrastructure.storage_paths import RESULTS_DIR


PIPELINE_RUN_LOG = RESULTS_DIR / "runtime" / "pipeline_runs.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_pipeline_log_exists() -> None:
    PIPELINE_RUN_LOG.parent.mkdir(parents=True, exist_ok=True)

    if not PIPELINE_RUN_LOG.exists():
        df = pd.DataFrame(
            columns=[
                "run_id",
                "pipeline_name",
                "step_name",
                "module_name",
                "status",
                "started_at_utc",
                "finished_at_utc",
                "duration_seconds",
                "error_message",
            ]
        )
        df.to_csv(PIPELINE_RUN_LOG, index=False)


def append_pipeline_record(record: dict) -> None:
    ensure_pipeline_log_exists()

    df = pd.read_csv(PIPELINE_RUN_LOG)
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(PIPELINE_RUN_LOG, index=False)


def save_failure_trace(run_id: str, step_name: str, error: Exception) -> Path:
    failure_dir = RESULTS_DIR / "runtime" / "failures"
    failure_dir.mkdir(parents=True, exist_ok=True)

    clean_step = step_name.replace(".", "_").replace(" ", "_")
    output_path = failure_dir / f"{run_id}_{clean_step}_failure.json"

    payload = {
        "run_id": run_id,
        "step_name": step_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "created_at_utc": utc_now(),
    }

    output_path.write_text(json.dumps(payload, indent=4), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    ensure_pipeline_log_exists()
    print(f"Pipeline runtime log ready: {PIPELINE_RUN_LOG}")
