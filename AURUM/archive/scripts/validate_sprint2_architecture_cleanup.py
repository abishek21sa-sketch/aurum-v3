from __future__ import annotations

import importlib
import json
from pathlib import Path


MODULES = [
    "src.config.storage_paths",
    "src.platform.dashboard_registry",
]

VALIDATORS = [
    Path("scripts/validate_core_quant.py"),
    Path("scripts/validate_realtime_stack.py"),
    Path("scripts/validate_portfolio_os.py"),
    Path("scripts/validate_ai_research_firm.py"),
    Path("scripts/validate_platform_complete.py"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 2 ARCHITECTURE CLEANUP VALIDATION")
    print("=" * 80)

    passed = True

    print("MODULE CHECKS")
    print("-" * 80)

    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"[PASS] import {module}")
        except Exception as exc:
            passed = False
            print(f"[FAIL] import {module}")
            print(f"       {exc}")

    print()
    print("STORAGE PATH CHECK")
    print("-" * 80)

    try:
        from src.config.storage_paths import ensure_storage_dirs, RESULTS_DIR, REPORTS_DIR, DATA_DIR

        ensure_storage_dirs()

        assert RESULTS_DIR.exists()
        assert REPORTS_DIR.exists()
        assert DATA_DIR.exists()

        print("[PASS] centralized storage paths active")
    except Exception as exc:
        passed = False
        print("[FAIL] centralized storage paths")
        print(f"       {exc}")

    print()
    print("DASHBOARD REGISTRY CHECK")
    print("-" * 80)

    try:
        from src.platform.dashboard_registry import DashboardRegistry

        result = DashboardRegistry().scan()

        assert result.official_dashboard == "institutional_command_center.py"
        assert result.status == "dashboard_registry_created"

        path = Path("results/sprint_cleanup/dashboard_registry.json")
        assert path.exists()

        print("[PASS] dashboard registry created")
        print(f"[INFO] archive candidates: {len(result.archived_candidates)}")
    except Exception as exc:
        passed = False
        print("[FAIL] dashboard registry")
        print(f"       {exc}")

    print()
    print("CONSOLIDATED VALIDATOR CHECK")
    print("-" * 80)

    for validator in VALIDATORS:
        if validator.exists():
            print(f"[PASS] {validator}")
        else:
            passed = False
            print(f"[FAIL] missing {validator}")

    print()
    print("SCHEMA CHECK")
    print("-" * 80)

    try:
        data = json.loads(Path("results/sprint_cleanup/dashboard_registry.json").read_text())
        assert data["official_dashboard"] == "institutional_command_center.py"
        assert data["status"] == "dashboard_registry_created"
        print("[PASS] dashboard registry schema")
    except Exception as exc:
        passed = False
        print("[FAIL] dashboard registry schema")
        print(f"       {exc}")

    print()
    print("=" * 80)
    if passed:
        print("[PASS] SPRINT 2 ARCHITECTURE CLEANUP FOUNDATION COMPLETE")
        print("Central paths, dashboard registry, and consolidated validators are in place.")
    else:
        print("[FAIL] SPRINT 2 ARCHITECTURE CLEANUP VALIDATION FAILED")
    print("=" * 80)


if __name__ == "__main__":
    main()