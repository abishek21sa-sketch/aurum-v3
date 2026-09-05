from datetime import datetime, timezone
from pathlib import Path
import json
import pandas as pd

from src.infrastructure.storage_paths import RESULTS_DIR


MANIFEST_PATH = RESULTS_DIR / "runtime" / "artifact_manifest.csv"


def ensure_manifest_exists() -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not MANIFEST_PATH.exists():
        df = pd.DataFrame(
            columns=[
                "created_at_utc",
                "artifact_path",
                "metadata_path",
                "layer",
                "artifact_type",
                "name",
                "file_extension",
                "rows",
                "columns",
                "characters",
                "source",
            ]
        )
        df.to_csv(MANIFEST_PATH, index=False)


def register_artifact(artifact_path: Path, metadata_path: Path) -> None:
    ensure_manifest_exists()

    metadata = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    record = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_path": str(artifact_path),
        "metadata_path": str(metadata_path),
        "layer": metadata.get("layer"),
        "artifact_type": metadata.get("artifact_type"),
        "name": metadata.get("name"),
        "file_extension": artifact_path.suffix.replace(".", ""),
        "rows": metadata.get("rows"),
        "columns": ",".join(metadata.get("columns", []))
        if isinstance(metadata.get("columns"), list)
        else metadata.get("columns"),
        "characters": metadata.get("characters"),
        "source": metadata.get("source"),
    }

    manifest_df = pd.read_csv(MANIFEST_PATH)
    manifest_df = pd.concat([manifest_df, pd.DataFrame([record])], ignore_index=True)
    manifest_df.to_csv(MANIFEST_PATH, index=False)


def read_manifest() -> pd.DataFrame:
    ensure_manifest_exists()
    return pd.read_csv(MANIFEST_PATH)


if __name__ == "__main__":
    ensure_manifest_exists()
    print(f"Artifact manifest ready: {MANIFEST_PATH}")