# src/portfolio/portfolio_operating_report.py

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


REPORT_DIR = Path("results/portfolio")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_PATH = REPORT_DIR / "portfolio_operating_report.json"
TEXT_REPORT_PATH = REPORT_DIR / "portfolio_operating_report.txt"


def load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


class PortfolioOperatingReport:
    def build_report(self) -> Dict[str, Any]:
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "report_type": "AURUM_INSTITUTIONAL_PORTFOLIO_OPERATING_REPORT",
            "portfolio_state": load_json("results/portfolio_state/institutional_portfolio_state.json"),
            "monitoring": {
                "performance_attribution": load_json("results/monitoring/performance_attribution_summary.json"),
                "strategy_attribution": load_json("results/monitoring/strategy_contribution_summary.json"),
                "benchmark_comparison": load_json("results/monitoring/benchmark_summary.json"),
                "portfolio_drift": load_json("results/monitoring/portfolio_drift_summary.json"),
                "risk_budget": load_json("results/monitoring/risk_budget_summary.json"),
            },
            "governance": {
                "approval": load_json("results/governance/portfolio_approval_decision.json"),
                "compliance": load_json("results/governance/compliance_summary.json"),
                "exposure_limits": load_json("results/governance/exposure_limit_summary.json"),
                "concentration": load_json("results/governance/concentration_summary.json"),
                "drawdown": load_json("results/governance/drawdown_governance_summary.json"),
                "liquidity": load_json("results/governance/liquidity_summary.json"),
            },
            "execution": {
                "cash_management": load_json("results/execution/cash_management_report.json"),
                "paper_trading": load_json("results/execution/paper_trading_summary.json"),
                "transaction_cost": load_json("results/execution/transaction_cost_summary.json"),
                "execution_priority": load_json("results/execution/execution_priority_summary.json"),
                "rebalance_decision": load_json("results/execution/rebalance_decision_summary.json"),
                "lifecycle": load_json("results/execution/lifecycle_report.json"),
            },
        }

        REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        self.write_text_report(report)
        return report

    def write_text_report(self, report: Dict[str, Any]) -> None:
        state_summary = report.get("portfolio_state", {}).get("state_summary", {})

        lines = [
            "=" * 80,
            "AURUM INSTITUTIONAL PORTFOLIO OPERATING REPORT",
            "=" * 80,
            "",
            f"Timestamp UTC: {report.get('timestamp_utc')}",
            "",
            "PORTFOLIO STATE",
            "-" * 80,
            f"Current portfolio loaded: {state_summary.get('has_current_portfolio')}",
            f"Target portfolio loaded: {state_summary.get('has_target_portfolio')}",
            f"Governance approval loaded: {state_summary.get('has_governance_approval')}",
            f"Execution lifecycle loaded: {state_summary.get('has_execution_lifecycle')}",
            "",
            "OPERATING LAYERS INCLUDED",
            "-" * 80,
            "Monitoring: performance, strategy attribution, benchmark, drift, risk budget",
            "Governance: approval, compliance, exposure, concentration, drawdown, liquidity",
            "Execution: cash, paper trading, transaction cost, priority, rebalance, lifecycle",
            "",
            "INTERPRETATION",
            "-" * 80,
            "AURUM has assembled a full institutional portfolio operating view from monitoring, governance, execution, and state-management layers.",
        ]

        TEXT_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    builder = PortfolioOperatingReport()
    report = builder.build_report()

    print("=" * 80)
    print("AURUM PORTFOLIO OPERATING REPORT")
    print("=" * 80)
    print("Report saved to:", REPORT_PATH)
    print("Text report saved to:", TEXT_REPORT_PATH)
    print("Sections:", list(report.keys()))


if __name__ == "__main__":
    main()