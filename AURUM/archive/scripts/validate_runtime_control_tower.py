import json
from pathlib import Path

import pandas as pd

from src.config.config_loader import load_config


def pass_check(name: str, detail: str = "") -> bool:
    print(f"[PASS] {name}")
    if detail:
        print(f"       {detail}")
    return True


def fail_check(name: str, detail: str = "") -> bool:
    print(f"[FAIL] {name}")
    if detail:
        print(f"       {detail}")
    return False


def validate_json(name: str, path: Path) -> bool:
    if not path.exists():
        return fail_check(name, f"Missing: {path}")

    if path.stat().st_size == 0:
        return fail_check(name, f"Empty file: {path}")

    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return fail_check(name, f"Invalid JSON: {exc}")

    return pass_check(name, f"path: {path}")


def validate_csv(name: str, path: Path) -> bool:
    if not path.exists():
        return fail_check(name, f"Missing: {path}")

    if path.stat().st_size == 0:
        return fail_check(name, f"Empty file: {path}")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return fail_check(name, f"Invalid CSV: {exc}")

    if df.empty:
        return fail_check(name, f"CSV has no rows: {path}")

    return pass_check(name, f"path: {path} | rows: {len(df)}")


def main() -> None:
    print("\nAURUM RUNTIME CONTROL TOWER VALIDATION")
    print("=" * 70)

    config = load_config()

    runtime_dir = Path(config["runtime"]["output_dir"])
    state_dir = runtime_dir / "state"

    checks = [
        validate_json("Runtime Manifest", runtime_dir / "runtime_manifest.json"),
        validate_json("Governance Decision", runtime_dir / "runtime_governance_decision.json"),
        validate_json("Drift Report", runtime_dir / "runtime_drift_report.json"),
        validate_csv("Runtime Health Summary", runtime_dir / "runtime_health_summary.csv"),
        validate_csv("Checkpoint Summary", runtime_dir / "runtime_checkpoint_summary.csv"),
        validate_json("Latest Runtime State", state_dir / "latest_runtime_state.json"),
    ]

    print("-" * 70)

    if all(checks):
        print("OVERALL STATUS: PASS")
    else:
        print("OVERALL STATUS: FAIL")


if __name__ == "__main__":
    main()