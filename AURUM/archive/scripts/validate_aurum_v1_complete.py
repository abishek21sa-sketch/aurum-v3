"""
AURUM V1 COMPLETE VALIDATOR

Validates that AURUM v1 is clean, runnable, explainable, and demo-ready.

Usage
-----
python -m scripts.validate_aurum_v1_complete
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, UTC


REQUIRED_FILES = [
    "scripts/run_aurum_v1_demo.py",
    "src/optimization/cvar_lp_optimizer.py",
    "src/regimes/hmm_regime_engine_clean.py",
    "src/intelligence/institutional_anomaly_detector.py",
    "src/config/storage_paths.py",
    "src/portfolio_os/portfolio_operating_system.py",
    "src/research_firm/ai_research_firm_mode.py",
]

REQUIRED_PRESENTATION_FILES = [
    "reports/aurum_v1_presentation_package/README_DRAFT.md",
    "reports/aurum_v1_presentation_package/ARCHITECTURE_DIAGRAM.md",
    "reports/aurum_v1_presentation_package/AURUM_WHITEPAPER_DRAFT.md",
    "reports/aurum_v1_presentation_package/RESUME_SUMMARY.md",
    "reports/aurum_v1_presentation_package/PACKAGE_INDEX.md",
]

REQUIRED_DEMO_OUTPUTS = [
    "reports/aurum_v1_demo/demo_run_summary.json",
    "reports/aurum_v1_demo/demo_console_report.txt",
]


def pass_msg(msg: str) -> None:
    print(f"[PASS] {msg}")


def fail_msg(msg: str) -> None:
    print(f"[FAIL] {msg}")


def check_file(path: str) -> bool:
    if Path(path).exists():
        pass_msg(path)
        return True

    fail_msg(path)
    return False


def run_demo() -> bool:
    print("\nRUNNING DEMO CHECK")
    print("-" * 80)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "scripts.run_aurum_v1_demo"],
            capture_output=True,
            text=True,
            check=True,
        )

        pass_msg("python -m scripts.run_aurum_v1_demo")
        return True

    except subprocess.CalledProcessError as exc:
        fail_msg("python -m scripts.run_aurum_v1_demo")
        print(exc.stdout[-3000:])
        print(exc.stderr[-3000:])
        return False


def validate_demo_summary() -> bool:
    print("\nDEMO SUMMARY CHECK")
    print("-" * 80)

    path = Path("reports/aurum_v1_demo/demo_run_summary.json")

    if not path.exists():
        fail_msg("demo_run_summary.json missing")
        return False

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail_msg(f"demo_run_summary.json invalid JSON: {exc}")
        return False

    steps = data.get("steps", [])

    if not steps:
        fail_msg("demo summary has no steps")
        return False

    failed = [s for s in steps if s.get("status") != "success"]

    if failed:
        fail_msg(f"{len(failed)} demo steps failed")
        for step in failed:
            print(f"       - {step.get('step')}")
        return False

    pass_msg(f"all demo steps passed: {len(steps)}")
    return True


def write_validation_report(status: str, checks_passed: int, checks_total: int) -> None:
    output_dir = Path("reports/aurum_v1_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "validator": "validate_aurum_v1_complete",
        "status": status,
        "checks_passed": checks_passed,
        "checks_total": checks_total,
    }

    path = output_dir / "aurum_v1_validation_report.json"
    path.write_text(json.dumps(report, indent=4), encoding="utf-8")


def main() -> None:
    print("=" * 80)
    print("AURUM V1 COMPLETE VALIDATION")
    print("=" * 80)

    checks: list[bool] = []

    print("\nCORE FILE CHECKS")
    print("-" * 80)
    for file in REQUIRED_FILES:
        checks.append(check_file(file))

    print("\nPRESENTATION PACKAGE CHECKS")
    print("-" * 80)
    for file in REQUIRED_PRESENTATION_FILES:
        checks.append(check_file(file))

    checks.append(run_demo())

    print("\nDEMO OUTPUT CHECKS")
    print("-" * 80)
    for file in REQUIRED_DEMO_OUTPUTS:
        checks.append(check_file(file))

    checks.append(validate_demo_summary())

    passed = sum(checks)
    total = len(checks)

    print("\n" + "=" * 80)

    if passed == total:
        status = "AURUM_V1_COMPLETE"
        print("[PASS] AURUM V1 COMPLETE")
    else:
        status = "AURUM_V1_INCOMPLETE"
        print("[FAIL] AURUM V1 INCOMPLETE")

    print(f"Checks Passed: {passed}/{total}")
    print("=" * 80)

    write_validation_report(status, passed, total)

    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()