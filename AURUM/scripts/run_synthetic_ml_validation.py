"""Run transparent, chronological ML baselines over the synthetic dataset."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.institutional.synthetic_ml import write_synthetic_ml_validation


def main() -> int:
    result = write_synthetic_ml_validation(ROOT)
    print(f"AURUM_SYNTHETIC_ML_VALIDATION={result['service']}")
    print(f"AURUM_SYNTHETIC_REGRESSION_R2={result['regression']['r_squared']:.6f}")
    print(f"AURUM_SYNTHETIC_CLASSIFICATION_ACCURACY={result['classification']['accuracy']:.6f}")
    print(f"AURUM_SYNTHETIC_PROMOTION={result['promotion_state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
