from pathlib import Path
import importlib
import subprocess
import sys


REQUIRED_MODULES = [
    "src.portfolio_os.portfolio_state_machine",
    "src.portfolio_os.portfolio_director",
    "src.portfolio_os.daily_portfolio_cycle",
    "src.portfolio_os.portfolio_operating_system",
    "src.market_data.market_data_service",
    "src.database.postgres_manager",
    "src.database.schema_initializer",
    "src.reliability.platform_health_monitor",
    "src.reliability.service_health_monitor",
    "src.reliability.alert_engine",
    "src.reliability.runtime_audit_engine",
    "src.reliability.institutional_readiness_score",
]

REQUIRED_FILES = [
    "dashboard/official_dashboard.py",
    "src/dashboard/institutional_command_center.py",
    "docker-compose.yml",
    "Dockerfile.api",
    "Dockerfile.dashboard",
    "MASTER_VISION.md",
    "SYSTEM_ARCHITECTURE.md",
    "DATA_PIPELINE.md",
    "PORTFOLIO_OS.md",
    "AI_COMMITTEE.md",
    "OPERATIONS_MANUAL.md",
]

REQUIRED_ARTIFACTS = [
    "results/portfolio_os/portfolio_directive.json",
    "results/portfolio_os/daily_portfolio_cycle.json",
    "results/portfolio_os/portfolio_operating_system.json",
    "results/reliability/platform_health_report.json",
    "results/reliability/service_health_report.json",
    "results/reliability/runtime_audit_report.json",
    "results/reliability/institutional_readiness_score.json",
]


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
        if detail:
            print(f"       {detail}")
    else:
        print(f"[FAIL] {label}")
        if detail:
            print(f"       {detail}")
        raise SystemExit(1)


def run_validator(module_name: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", module_name],
        capture_output=True,
        text=True,
    )

    check(
        result.returncode == 0,
        f"{module_name} passed",
        result.stdout.splitlines()[-1] if result.stdout else result.stderr,
    )


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6A COMPLETE VALIDATION")
    print("=" * 80)

    print("\nMODULE CHECKS")
    print("-" * 80)
    for module in REQUIRED_MODULES:
        importlib.import_module(module)
        check(True, f"import {module}")

    print("\nFILE CHECKS")
    print("-" * 80)
    for file in REQUIRED_FILES:
        check(Path(file).exists(), f"{file} exists")

    print("\nARTIFACT CHECKS")
    print("-" * 80)
    for artifact in REQUIRED_ARTIFACTS:
        check(Path(artifact).exists(), f"{artifact} exists")

    print("\nVALIDATOR CHECKS")
    print("-" * 80)
    run_validator("scripts.validate_phase6a5_reliability_layer")
    run_validator("scripts.validate_phase6a6_deployment_layer")
    run_validator("scripts.validate_phase6a7_documentation_layer")

    print("=" * 80)
    print("[PASS] PHASE 6A INSTITUTIONAL ENGINEERING COMPLETE")
    print("AURUM is now an Institutional Market Operating System.")
    print("=" * 80)


if __name__ == "__main__":
    main()