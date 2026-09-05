from __future__ import annotations

import importlib
import json
from pathlib import Path


REQUIRED_MODULES = [
    "src.platform.dashboard_registry",
    "src.platform.dashboard_launcher",
]

REQUIRED_ARTIFACTS = [
    Path("results/sprint_cleanup/dashboard_registry.json"),
    Path("results/sprint_cleanup/dashboard_launch_plan.json"),
    Path("results/sprint_cleanup/dashboard_archive_manifest.json"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM SPRINT 2C DASHBOARD CONSOLIDATION VALIDATION")
    print("=" * 80)

    passed = True

    print("MODULE CHECKS")
    print("-" * 80)

    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
            print(f"[PASS] import {module}")
        except Exception as exc:
            passed = False
            print(f"[FAIL] import {module}")
            print(f"       {exc}")

    print()
    print("DASHBOARD REGISTRY CHECK")
    print("-" * 80)

    try:
        from src.platform.dashboard_registry import DashboardRegistry

        registry = DashboardRegistry().scan()

        assert registry.official_dashboard == "institutional_command_center.py"
        assert registry.status == "dashboard_registry_created"

        print("[PASS] official dashboard registered")
        print(f"[INFO] archive candidates: {len(registry.archived_candidates)}")
    except Exception as exc:
        passed = False
        print("[FAIL] dashboard registry")
        print(f"       {exc}")

    print()
    print("DASHBOARD LAUNCH PLAN CHECK")
    print("-" * 80)

    try:
        from src.platform.dashboard_launcher import DashboardLauncher

        plan = DashboardLauncher().build_launch_plan()

        assert plan.official_dashboard == "institutional_command_center.py"
        assert plan.status in {
            "official_dashboard_ready",
            "official_dashboard_missing",
        }

        if plan.status == "official_dashboard_ready":
            assert plan.official_dashboard_path is not None
            assert Path(plan.official_dashboard_path).exists()
            assert plan.launch_command

            print("[PASS] official dashboard launch plan ready")
            print(f"[INFO] dashboard path: {plan.official_dashboard_path}")
        else:
            passed = False
            print("[FAIL] official dashboard missing")
            print("       expected institutional_command_center.py somewhere under src/, dashboards/, or streamlit/")

    except Exception as exc:
        passed = False
        print("[FAIL] dashboard launch plan")
        print(f"       {exc}")

    print()
    print("ARCHIVE MANIFEST CHECK")
    print("-" * 80)

    try:
        from scripts.generate_dashboard_archive_manifest import generate_manifest

        manifest = generate_manifest()

        assert manifest.official_dashboard == "institutional_command_center.py"
        assert manifest.status == "dashboard_archive_manifest_created"
        assert manifest.archive_count >= 0

        print("[PASS] dashboard archive manifest generated")
        print(f"[INFO] archive candidates: {manifest.archive_count}")
    except Exception as exc:
        passed = False
        print("[FAIL] dashboard archive manifest")
        print(f"       {exc}")

    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)

    for artifact in REQUIRED_ARTIFACTS:
        if artifact.exists():
            print(f"[PASS] {artifact}")
        else:
            passed = False
            print(f"[FAIL] missing {artifact}")

    print()
    print("SCHEMA CHECKS")
    print("-" * 80)

    try:
        registry = json.loads(
            Path("results/sprint_cleanup/dashboard_registry.json").read_text()
        )
        assert registry["official_dashboard"] == "institutional_command_center.py"
        assert registry["status"] == "dashboard_registry_created"
        print("[PASS] dashboard registry schema")
    except Exception as exc:
        passed = False
        print("[FAIL] dashboard registry schema")
        print(f"       {exc}")

    try:
        plan = json.loads(
            Path("results/sprint_cleanup/dashboard_launch_plan.json").read_text()
        )
        assert plan["official_dashboard"] == "institutional_command_center.py"
        assert plan["status"] == "official_dashboard_ready"
        assert plan["official_dashboard_path"]
        print("[PASS] dashboard launch plan schema")
    except Exception as exc:
        passed = False
        print("[FAIL] dashboard launch plan schema")
        print(f"       {exc}")

    try:
        manifest = json.loads(
            Path("results/sprint_cleanup/dashboard_archive_manifest.json").read_text()
        )
        assert manifest["official_dashboard"] == "institutional_command_center.py"
        assert manifest["status"] == "dashboard_archive_manifest_created"
        print("[PASS] dashboard archive manifest schema")
    except Exception as exc:
        passed = False
        print("[FAIL] dashboard archive manifest schema")
        print(f"       {exc}")

    print()
    print("=" * 80)

    if passed:
        print("[PASS] SPRINT 2C DASHBOARD CONSOLIDATION COMPLETE")
        print("AURUM now has a single official dashboard entrypoint and archive manifest.")
    else:
        print("[FAIL] SPRINT 2C DASHBOARD CONSOLIDATION FAILED")

    print("=" * 80)

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()