from pathlib import Path
import pandas as pd

from src.infrastructure.storage_paths import DATA_DIR, RESULTS_DIR
from src.infrastructure.artifact_manifest import MANIFEST_PATH, read_manifest
from src.infrastructure.validate_config import validate_environment

REQUIRED_DATA_DIRS = [
    "raw",
    "processed",
    "features",
    "regimes",
    "forecasts",
    "allocations",
    "backtests",
    "live",
]

REQUIRED_RESULTS_DIRS = [
    "reports",
    "figures",
    "logs",
    "runtime",
]


def check_directories(base_dir: Path, required_dirs: list[str]) -> list[str]:
    missing = []

    for directory in required_dirs:
        path = base_dir / directory
        if not path.exists() or not path.is_dir():
            missing.append(str(path))

    return missing


def validate_manifest() -> list[str]:
    issues = []

    if not MANIFEST_PATH.exists():
        issues.append(f"Missing manifest file: {MANIFEST_PATH}")
        return issues

    manifest = read_manifest()

    required_columns = [
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

    missing_columns = [col for col in required_columns if col not in manifest.columns]

    if missing_columns:
        issues.append(f"Manifest missing columns: {missing_columns}")

    return issues


def validate_storage_layer() -> None:
    issues = []

    issues.extend(check_directories(DATA_DIR, REQUIRED_DATA_DIRS))
    issues.extend(check_directories(RESULTS_DIR, REQUIRED_RESULTS_DIRS))
    issues.extend(validate_manifest())

    if issues:
        print("STORAGE VALIDATION FAILED")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    print("STORAGE VALIDATION PASSED")
    print(f"Data directory: {DATA_DIR}")
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Manifest: {MANIFEST_PATH}")

    print("\nVALIDATING CONFIGS")
    for env in ["dev", "research", "prod"]:
        validate_environment(env)


if __name__ == "__main__":
    validate_storage_layer()