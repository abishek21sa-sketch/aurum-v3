"""Generate the deterministic 10,000-row AURUM synthetic ML dataset."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.institutional.synthetic_ml import DEFAULT_ROW_COUNT, DEFAULT_SEED, generate_synthetic_dataset


def main() -> int:
    manifest = generate_synthetic_dataset(ROOT, row_count=DEFAULT_ROW_COUNT, seed=DEFAULT_SEED)
    print(f"AURUM_SYNTHETIC_DATASET={manifest['actual_rows']}_ROWS")
    print(f"AURUM_SYNTHETIC_SEED={manifest['seed']}")
    print(f"AURUM_SYNTHETIC_DATA_CLASS={manifest['data_class']}")
    print(f"AURUM_SYNTHETIC_SHA256={manifest['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
