from pathlib import Path
import importlib


MODULES = [
    "src.governance.portfolio_policy_engine",
    "src.governance.exposure_limit_monitor",
    "src.governance.portfolio_compliance_engine",
    "src.governance.concentration_risk_engine",
    "src.governance.liquidity_governance_engine",
    "src.governance.drawdown_governance_engine",
    "src.governance.investment_committee_engine",
    "src.governance.governance_escalation_engine",
    "src.governance.portfolio_approval_gate",
    "src.governance.governance_report_generator",
]

OUTPUTS = [
    "results/governance/policy_constraints.json",
    "results/governance/exposure_limit_report.csv",
    "results/governance/exposure_limit_summary.json",
    "results/governance/compliance_report.csv",
    "results/governance/compliance_summary.json",
    "results/governance/concentration_report.csv",
    "results/governance/concentration_summary.json",
    "results/governance/liquidity_report.csv",
    "results/governance/liquidity_summary.json",
    "results/governance/drawdown_governance_report.csv",
    "results/governance/drawdown_governance_summary.json",
    "results/governance/investment_committee_decision.json",
    "results/governance/governance_escalations.json",
    "results/governance/portfolio_approval_decision.json",
    "results/governance/institutional_governance_report.csv",
    "results/governance/institutional_governance_summary.json",
]


def check_imports() -> bool:
    print("\nMODULE IMPORT CHECKS")
    print("-" * 80)

    passed = True

    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"[PASS] {module}")
        except Exception as e:
            passed = False
            print(f"[FAIL] {module}")
            print(f"       {e}")

    return passed


def check_outputs() -> bool:
    print("\nOUTPUT EXISTENCE CHECKS")
    print("-" * 80)

    passed = True

    for output in OUTPUTS:
        path = Path(output)

        if path.exists():
            print(f"[PASS] {output}")
        else:
            passed = False
            print(f"[FAIL] {output}")

    return passed


def main() -> None:
    print("=" * 80)
    print("AURUM GOVERNANCE LAYER VALIDATION")
    print("=" * 80)

    imports_ok = check_imports()
    outputs_ok = check_outputs()

    print("\nVALIDATION RESULT")
    print("-" * 80)

    if imports_ok and outputs_ok:
        print("[PASS] Governance layer validation complete.")
    else:
        print("[FAIL] Governance layer validation failed.")


if __name__ == "__main__":
    main()