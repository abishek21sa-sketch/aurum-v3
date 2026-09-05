from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict
import json

from src.portfolio_lab_2.scenario_library import ScenarioLibrary


RESULTS_DIR = Path("results/portfolio_lab_2")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PortfolioLabEngine:
    def __init__(self) -> None:
        self.current_weights = {
            "SPY": 0.1960,
            "QQQ": 0.1869,
            "TLT": 0.2067,
            "GLD": 0.1352,
            "BTC-USD": 0.0291,
            "CASH": 0.2461,
        }

    def scenario_impact(self, scenario: Dict) -> Dict:
        shocks = scenario["asset_shocks"]

        asset_impacts = {}
        total_impact = 0.0

        for asset, weight in self.current_weights.items():
            shock = shocks.get(asset, 0.0)
            impact = weight * shock
            asset_impacts[asset] = {
                "weight": weight,
                "shock": shock,
                "impact": round(impact, 6),
            }
            total_impact += impact

        total_impact = round(total_impact, 6)

        if total_impact <= -0.08:
            severity = "critical"
        elif total_impact <= -0.04:
            severity = "high"
        elif total_impact <= -0.02:
            severity = "medium"
        else:
            severity = "low"

        return {
            "scenario_id": scenario["scenario_id"],
            "name": scenario["name"],
            "question": scenario["question"],
            "shock_type": scenario["shock_type"],
            "portfolio_impact": total_impact,
            "severity": severity,
            "asset_impacts": asset_impacts,
            "institutional_logic": scenario["institutional_logic"],
            "recommended_response": self.recommended_response(severity, scenario["shock_type"]),
        }

    def recommended_response(self, severity: str, shock_type: str) -> str:
        if severity == "critical":
            return "Escalate to committee, reduce risk exposure, increase cash and defensive hedges."

        if severity == "high":
            return "Review portfolio immediately, reduce vulnerable exposures, and prepare defensive rebalance."

        if shock_type in {"rates_shock", "macro_inflation"}:
            return "Monitor duration and growth exposure; consider inflation and commodity hedges."

        if shock_type == "crypto_crash":
            return "Limit crypto beta and monitor spillover into growth assets."

        return "Monitor scenario exposure and maintain current risk controls."

    def run(self) -> Dict:
        library = ScenarioLibrary().save()
        results = [
            self.scenario_impact(scenario)
            for scenario in library["scenarios"]
        ]

        ranked = sorted(
            results,
            key=lambda row: row["portfolio_impact"],
        )

        summary = {
            "timestamp": utc_now(),
            "lab": "aurum_portfolio_lab_2",
            "scenario_count": len(results),
            "worst_scenario": ranked[0] if ranked else None,
            "critical_count": len([r for r in results if r["severity"] == "critical"]),
            "high_count": len([r for r in results if r["severity"] == "high"]),
            "medium_count": len([r for r in results if r["severity"] == "medium"]),
            "low_count": len([r for r in results if r["severity"] == "low"]),
            "scenario_results": ranked,
        }

        (RESULTS_DIR / "portfolio_lab_results.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )

        return summary


def main() -> None:
    result = PortfolioLabEngine().run()
    worst = result["worst_scenario"]

    print("=" * 80)
    print("AURUM PHASE 6B.7 PORTFOLIO LABORATORY 2.0")
    print("=" * 80)
    print(f"Scenarios:       {result['scenario_count']}")
    print(f"Critical:        {result['critical_count']}")
    print(f"High:            {result['high_count']}")
    print(f"Medium:          {result['medium_count']}")
    print(f"Low:             {result['low_count']}")
    if worst:
        print("-" * 80)
        print(f"Worst Scenario:  {worst['scenario_id']} | {worst['name']}")
        print(f"Impact:          {worst['portfolio_impact']:.2%}")
        print(f"Severity:        {worst['severity']}")
        print(f"Response:        {worst['recommended_response']}")
    print("=" * 80)


if __name__ == "__main__":
    main()