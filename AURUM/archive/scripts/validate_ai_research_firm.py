from __future__ import annotations

import importlib
from pathlib import Path


MODULES = [
    "src.research_firm.ai_research_firm_mode",
    "src.institutional.daily_institutional_cycle",
    "src.institutional.daily_institutional_report_generator",
    "src.cio.chief_investment_officer_agent",
    "src.cio.quant_core_cio_briefing_adapter",
]


ARTIFACTS = [
    Path("results/research_firm/ai_research_firm_mode.json"),
    Path("results/research_firm/daily_research_firm_state.json"),
    Path("results/sprint1b/quant_core_cio_briefing.json"),
]


def main() -> None:
    print("=" * 80)
    print("AURUM AI RESEARCH FIRM VALIDATION")
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
    print("ARTIFACT CHECKS")
    print("-" * 80)
    for artifact in ARTIFACTS:
        if artifact.exists():
            print(f"[PASS] {artifact}")
        else:
            passed = False
            print(f"[FAIL] missing {artifact}")

    print()
    print("=" * 80)
    print("[PASS] AI RESEARCH FIRM VALIDATION COMPLETE" if passed else "[FAIL] AI RESEARCH FIRM VALIDATION FAILED")
    print("=" * 80)


if __name__ == "__main__":
    main()