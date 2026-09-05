from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import List, Tuple


STATE_MACHINE_JSON = Path("results/portfolio_os/portfolio_state_machine.json")
PORTFOLIO_DIRECTIVE_JSON = Path("results/portfolio_os/portfolio_directive.json")
DAILY_CYCLE_JSON = Path("results/portfolio_os/daily_portfolio_cycle.json")
PORTFOLIO_OS_JSON = Path("results/portfolio_os/portfolio_operating_system.json")
PORTFOLIO_OS_TXT = Path("results/portfolio_os/portfolio_operating_system_report.txt")


MODULES = [
    "src.portfolio_os.portfolio_state_machine",
    "src.portfolio_os.portfolio_director",
    "src.portfolio_os.daily_portfolio_cycle",
    "src.portfolio_os.portfolio_operating_system",
]


def print_result(name: str, passed: bool, detail: str = "") -> None:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")
    if detail:
        print(f"       {detail}")


def check_imports() -> List[Tuple[str, bool, str]]:
    results = []

    for module in MODULES:
        try:
            importlib.import_module(module)
            results.append((module, True, "import ok"))
        except Exception as exc:
            results.append((module, False, str(exc)))

    return results


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_state_machine() -> Tuple[bool, str]:
    try:
        from src.portfolio_os.portfolio_state_machine import PortfolioStateMachine

        machine = PortfolioStateMachine()
        snapshot = machine.run_full_cycle()

        if snapshot["current_state"] != "COMPLETE":
            return False, f"unexpected final state {snapshot['current_state']}"

        if snapshot["state_count"] != 9:
            return False, f"unexpected state count {snapshot['state_count']}"

        return True, "state machine completed full workflow"

    except Exception as exc:
        return False, str(exc)


def validate_director() -> Tuple[bool, str]:
    try:
        from src.portfolio_os.portfolio_director import PortfolioDirector

        directive = PortfolioDirector().generate_directive()

        if directive["portfolio_posture"] != "defensive":
            return False, "unexpected portfolio posture"

        if directive["execution_permission"] != "blocked":
            return False, "unexpected execution permission"

        return True, "portfolio director generated directive"

    except Exception as exc:
        return False, str(exc)


def validate_daily_cycle() -> Tuple[bool, str]:
    try:
        from src.portfolio_os.daily_portfolio_cycle import DailyPortfolioCycle

        cycle = DailyPortfolioCycle().run()

        if cycle["status"] != "COMPLETE":
            return False, "daily cycle did not complete"

        required_stages = {
            "research",
            "committee",
            "memory",
            "decision_intelligence",
            "governance",
            "portfolio_action",
            "learning",
        }

        missing = required_stages - set(cycle.get("stages", {}).keys())

        if missing:
            return False, f"missing stages: {sorted(missing)}"

        return True, "daily portfolio cycle completed all stages"

    except Exception as exc:
        return False, str(exc)


def validate_operating_system() -> Tuple[bool, str]:
    try:
        from src.portfolio_os.portfolio_operating_system import PortfolioOperatingSystem

        state = PortfolioOperatingSystem().run()

        if state["status"] != "COMPLETE":
            return False, "portfolio OS did not complete"

        if state["execution_permission"] != "blocked":
            return False, "unexpected execution permission"

        if not PORTFOLIO_OS_TXT.exists():
            return False, "portfolio OS report missing"

        return True, "portfolio operating system completed"

    except Exception as exc:
        return False, str(exc)


def validate_report_content() -> Tuple[bool, str]:
    if not PORTFOLIO_OS_TXT.exists():
        return False, "portfolio OS txt report missing"

    text = PORTFOLIO_OS_TXT.read_text(encoding="utf-8")

    required = [
        "AURUM PORTFOLIO OPERATING SYSTEM REPORT",
        "OPERATING STATE",
        "RISK OFFICER VIEW",
        "GOVERNANCE VIEW",
        "MEMORY VIEW",
        "LEARNING VIEW",
        "RECOMMENDED ACTIONS",
        "CYCLE STAGES",
    ]

    missing = [item for item in required if item not in text]

    if missing:
        return False, f"missing report sections: {missing}"

    return True, "portfolio OS report content valid"


def validate_artifacts() -> List[Tuple[str, bool, str]]:
    return [
        ("state machine json", STATE_MACHINE_JSON.exists(), str(STATE_MACHINE_JSON)),
        ("portfolio directive json", PORTFOLIO_DIRECTIVE_JSON.exists(), str(PORTFOLIO_DIRECTIVE_JSON)),
        ("daily portfolio cycle json", DAILY_CYCLE_JSON.exists(), str(DAILY_CYCLE_JSON)),
        ("portfolio operating system json", PORTFOLIO_OS_JSON.exists(), str(PORTFOLIO_OS_JSON)),
        ("portfolio operating system txt", PORTFOLIO_OS_TXT.exists(), str(PORTFOLIO_OS_TXT)),
    ]


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6A PORTFOLIO OPERATING SYSTEM VALIDATION")
    print("=" * 80)

    overall_pass = True

    print()
    print("MODULE IMPORT CHECKS")
    print("-" * 80)

    for module, passed, detail in check_imports():
        print_result(module, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("FUNCTIONAL CHECKS")
    print("-" * 80)

    for name, validator in [
        ("portfolio state machine", validate_state_machine),
        ("portfolio director", validate_director),
        ("daily portfolio cycle", validate_daily_cycle),
        ("portfolio operating system", validate_operating_system),
        ("portfolio OS report content", validate_report_content),
    ]:
        passed, detail = validator()
        print_result(name, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("ARTIFACT CHECKS")
    print("-" * 80)

    for name, passed, detail in validate_artifacts():
        print_result(name, passed, detail)
        overall_pass = overall_pass and passed

    print()
    print("=" * 80)

    if overall_pass:
        print("[PASS] PHASE 6A PORTFOLIO OPERATING SYSTEM COMPLETE")
        print("AURUM now runs the full portfolio workflow from one operating command.")
    else:
        print("[FAIL] PHASE 6A PORTFOLIO OPERATING SYSTEM NEEDS ATTENTION")

    print("=" * 80)

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()