from datetime import datetime, timezone
from pathlib import Path
import json
import pandas as pd

from src.infrastructure.storage_paths import get_data_path, get_result_path
from src.infrastructure.artifact_manifest import register_artifact

def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_artifact_name(
    artifact_type: str,
    name: str,
    extension: str,
    timestamped: bool = True,
) -> str:
    clean_type = artifact_type.lower().strip().replace(" ", "_")
    clean_name = name.lower().strip().replace(" ", "_")
    clean_extension = extension.lstrip(".")

    if timestamped:
        return f"{clean_type}_{clean_name}_{utc_timestamp()}.{clean_extension}"

    return f"{clean_type}_{clean_name}.{clean_extension}"


def write_metadata(metadata_path: Path, metadata: dict) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        **metadata,
    }

    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)


def save_dataframe_artifact(
    df: pd.DataFrame,
    layer: str,
    artifact_type: str,
    name: str,
    metadata: dict | None = None,
    timestamped: bool = True,
) -> Path:
    filename = build_artifact_name(
        artifact_type=artifact_type,
        name=name,
        extension="parquet",
        timestamped=timestamped,
    )

    output_path = get_data_path(layer, filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(output_path, index=False)

    metadata_path = output_path.with_suffix(".metadata.json")
    write_metadata(
        metadata_path,
        {
            "artifact_path": str(output_path),
            "layer": layer,
            "artifact_type": artifact_type,
            "name": name,
            "rows": int(len(df)),
            "columns": list(df.columns),
            **(metadata or {}),
        },
    )

    register_artifact(output_path, metadata_path)

    return output_path


def save_text_artifact(
    text: str,
    layer: str,
    artifact_type: str,
    name: str,
    metadata: dict | None = None,
    timestamped: bool = True,
) -> Path:
    filename = build_artifact_name(
        artifact_type=artifact_type,
        name=name,
        extension="txt",
        timestamped=timestamped,
    )

    output_path = get_result_path(layer, filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(text, encoding="utf-8")

    metadata_path = output_path.with_suffix(".metadata.json")
    write_metadata(
        metadata_path,
        {
            "artifact_path": str(output_path),
            "layer": layer,
            "artifact_type": artifact_type,
            "name": name,
            "characters": len(text),
            **(metadata or {}),
        },
    )

    register_artifact(output_path, metadata_path)
    return output_path