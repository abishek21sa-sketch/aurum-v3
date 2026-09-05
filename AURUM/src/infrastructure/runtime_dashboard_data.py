from pathlib import Path
import pandas as pd
from datetime import datetime, timezone
import json

from src.infrastructure.pipeline_runtime import PIPELINE_RUN_LOG
from src.infrastructure.artifact_manifest import MANIFEST_PATH
from src.infrastructure.storage_paths import RESULTS_DIR

DASHBOARD_SNAPSHOT_PATH = RESULTS_DIR / "runtime" / "runtime_dashboard_snapshot.json"

def load_pipeline_runs() -> pd.DataFrame:
    if not PIPELINE_RUN_LOG.exists():
        return pd.DataFrame()

    return pd.read_csv(PIPELINE_RUN_LOG)


def load_artifact_manifest() -> pd.DataFrame:
    if not MANIFEST_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(MANIFEST_PATH)


def summarize_pipeline_runs() -> dict:
    df = load_pipeline_runs()

    if df.empty:
        return {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "latest_run_id": None,
            "latest_pipeline": None,
            "latest_status": None,
            "average_step_duration_seconds": None,
        }

    latest_run_id = df.iloc[-1]["run_id"]
    latest_run = df[df["run_id"] == latest_run_id]

    failed_count = int((latest_run["status"] == "failed").sum())
    latest_status = "failed" if failed_count > 0 else "success"

    return {
        "total_steps": int(len(df)),
        "successful_steps": int((df["status"] == "success").sum()),
        "failed_steps": int((df["status"] == "failed").sum()),
        "latest_run_id": latest_run_id,
        "latest_pipeline": latest_run.iloc[0]["pipeline_name"],
        "latest_status": latest_status,
        "average_step_duration_seconds": float(df["duration_seconds"].mean()),
    }


def summarize_artifacts() -> dict:
    df = load_artifact_manifest()

    if df.empty:
        return {
            "total_artifacts": 0,
            "artifact_types": {},
            "layers": {},
            "latest_artifact": None,
        }

    return {
        "total_artifacts": int(len(df)),
        "artifact_types": df["artifact_type"].value_counts().to_dict(),
        "layers": df["layer"].value_counts().to_dict(),
        "latest_artifact": df.iloc[-1]["artifact_path"],
    }


def get_latest_pipeline_steps(limit: int = 20) -> list[dict]:
    df = load_pipeline_runs()

    if df.empty:
        return []

    latest = df.tail(limit).copy()
    return latest.to_dict(orient="records")


def build_runtime_dashboard_snapshot() -> dict:
    return {
        "pipeline_summary": summarize_pipeline_runs(),
        "artifact_summary": summarize_artifacts(),
        "latest_pipeline_steps": get_latest_pipeline_steps(),
    }

def save_runtime_dashboard_snapshot() -> dict:
    snapshot = build_runtime_dashboard_snapshot()
    snapshot["created_at_utc"] = datetime.now(timezone.utc).isoformat()

    DASHBOARD_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with DASHBOARD_SNAPSHOT_PATH.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=4, default=str)

    return snapshot

if __name__ == "__main__":
    snapshot = save_runtime_dashboard_snapshot()
    print(f"Saved snapshot: {DASHBOARD_SNAPSHOT_PATH}")

    print("AURUM RUNTIME DASHBOARD SNAPSHOT")
    print("=" * 80)

    print("\nPipeline Summary")
    print(snapshot["pipeline_summary"])

    print("\nArtifact Summary")
    print(snapshot["artifact_summary"])

    print("\nLatest Pipeline Steps")
    for row in snapshot["latest_pipeline_steps"][-5:]:
        print(row)
