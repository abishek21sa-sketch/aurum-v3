# src/digital_twin/digital_twin_report_generator.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


MONTE_CARLO_SUMMARY_PATH = Path(
    "results/digital_twin/monte_carlo_lab/monte_carlo_summary.json"
)

STRESS_TEST_PATH = Path(
    "results/digital_twin/stress_testing/stress_test_results.csv"
)

CONTAGION_PATH = Path(
    "results/digital_twin/contagion_engine/contagion_results.csv"
)

REGIME_TRANSITION_PATH = Path(
    "results/digital_twin/regime_transition/regime_transition_summary.json"
)

HISTORICAL_REPLAY_PATH = Path(
    "results/digital_twin/historical_replay/historical_replay_results.csv"
)

OUTPUT_DIR = Path("results/digital_twin/final_report")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class DigitalTwinReportGenerator:
    def load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}

        return json.loads(path.read_text(encoding="utf-8"))

    def load_csv(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame()

        return pd.read_csv(path)

    def classify_overall_status(
        self,
        monte_carlo: Dict[str, Any],
        worst_stress_impact: float,
        worst_contagion_impact: float,
        regime_risk_level: str,
    ) -> str:
        survival = monte_carlo.get("survival_status", "UNKNOWN")

        if (
            survival == "FRAGILE"
            or worst_stress_impact <= -0.30
            or worst_contagion_impact <= -0.25
            or regime_risk_level == "HIGH"
        ):
            return "FRAGILE"

        if (
            survival == "STRESSED"
            or worst_stress_impact <= -0.15
            or worst_contagion_impact <= -0.15
            or regime_risk_level == "MODERATE"
        ):
            return "STRESSED"

        return "ROBUST"

    def run(self) -> Dict[str, Any]:
        monte_carlo = self.load_json(MONTE_CARLO_SUMMARY_PATH)
        stress_df = self.load_csv(STRESS_TEST_PATH)
        contagion_df = self.load_csv(CONTAGION_PATH)
        regime = self.load_json(REGIME_TRANSITION_PATH)
        replay_df = self.load_csv(HISTORICAL_REPLAY_PATH)

        worst_stress = {}
        best_stress = {}
        worst_contagion = {}

        worst_stress_impact = 0.0
        worst_contagion_impact = 0.0

        if not stress_df.empty:
            stress_df = stress_df.sort_values("portfolio_impact")
            worst_stress = stress_df.iloc[0].to_dict()
            best_stress = stress_df.iloc[-1].to_dict()
            worst_stress_impact = float(worst_stress["portfolio_impact"])

        if not contagion_df.empty:
            contagion_df = contagion_df.sort_values("total_portfolio_impact")
            worst_contagion = contagion_df.iloc[0].to_dict()
            worst_contagion_impact = float(
                worst_contagion["total_portfolio_impact"]
            )

        regime_risk_level = regime.get("regime_risk_level", "UNKNOWN")

        overall_status = self.classify_overall_status(
            monte_carlo=monte_carlo,
            worst_stress_impact=worst_stress_impact,
            worst_contagion_impact=worst_contagion_impact,
            regime_risk_level=regime_risk_level,
        )

        final_summary = {
            "overall_digital_twin_status": overall_status,
            "monte_carlo": monte_carlo,
            "worst_stress_scenario": worst_stress,
            "best_stress_scenario": best_stress,
            "worst_contagion_source": worst_contagion,
            "regime_transition": regime,
            "historical_replay_available": not replay_df.empty,
        }

        self.write_outputs(
            final_summary=final_summary,
            stress_df=stress_df,
            contagion_df=contagion_df,
            replay_df=replay_df,
        )

        return final_summary

    def write_outputs(
        self,
        final_summary: Dict[str, Any],
        stress_df: pd.DataFrame,
        contagion_df: pd.DataFrame,
        replay_df: pd.DataFrame,
    ) -> None:
        json_path = OUTPUT_DIR / "digital_twin_final_summary.json"
        txt_path = OUTPUT_DIR / "digital_twin_final_report.txt"

        json_path.write_text(
            json.dumps(final_summary, indent=2),
            encoding="utf-8",
        )

        monte_carlo = final_summary.get("monte_carlo", {})
        worst_stress = final_summary.get("worst_stress_scenario", {})
        best_stress = final_summary.get("best_stress_scenario", {})
        worst_contagion = final_summary.get("worst_contagion_source", {})
        regime = final_summary.get("regime_transition", {})

        lines: List[str] = [
            "=" * 80,
            "AURUM MARKET DIGITAL TWIN FINAL REPORT",
            "=" * 80,
            "",
            f"Overall Digital Twin Status: {final_summary['overall_digital_twin_status']}",
            "",
            "-" * 80,
            "1. MONTE CARLO FUTURE WORLDS",
            "-" * 80,
            f"Simulations: {monte_carlo.get('simulations')}",
            f"Horizon Days: {monte_carlo.get('horizon_days')}",
            f"Expected Cumulative Return: {monte_carlo.get('expected_cumulative_return')}",
            f"Expected Annualized Volatility: {monte_carlo.get('expected_annualized_volatility')}",
            f"Expected Max Drawdown: {monte_carlo.get('expected_max_drawdown')}",
            f"VaR 95: {monte_carlo.get('var_95')}",
            f"CVaR 95: {monte_carlo.get('cvar_95')}",
            f"Probability of Loss: {monte_carlo.get('probability_of_loss')}",
            f"Survival Status: {monte_carlo.get('survival_status')}",
            "",
            "-" * 80,
            "2. STRESS TESTING",
            "-" * 80,
            f"Worst Scenario: {worst_stress.get('scenario_id')}",
            f"Worst Scenario Impact: {worst_stress.get('portfolio_impact')}",
            f"Worst Scenario Status: {worst_stress.get('survival_status')}",
            f"Worst Scenario Governance Action: {worst_stress.get('governance_action')}",
            "",
            f"Best Scenario: {best_stress.get('scenario_id')}",
            f"Best Scenario Impact: {best_stress.get('portfolio_impact')}",
            "",
            "-" * 80,
            "3. CONTAGION ENGINE",
            "-" * 80,
            f"Worst Contagion Source: {worst_contagion.get('source_asset')}",
            f"Total Portfolio Impact: {worst_contagion.get('total_portfolio_impact')}",
            f"Direct Impact: {worst_contagion.get('direct_portfolio_impact')}",
            f"Propagated Impact: {worst_contagion.get('propagated_portfolio_impact')}",
            f"Network Stress Level: {worst_contagion.get('network_stress_level')}",
            f"Governance Action: {worst_contagion.get('governance_action')}",
            "",
            "-" * 80,
            "4. REGIME TRANSITION SIMULATOR",
            "-" * 80,
            f"Current Regime: {regime.get('current_regime')}",
            f"Most Likely Next Regime: {regime.get('most_likely_next_regime')}",
            f"Transition Probability: {regime.get('transition_probability')}",
            f"Risk-On Probability: {regime.get('risk_on_probability')}",
            f"Risk-Off Probability: {regime.get('risk_off_probability')}",
            f"Panic Probability: {regime.get('panic_probability')}",
            f"Regime Risk Level: {regime.get('regime_risk_level')}",
            "",
            "-" * 80,
            "5. HISTORICAL REPLAY",
            "-" * 80,
            f"Historical Replay Available: {final_summary.get('historical_replay_available')}",
            "",
            "Note:",
            "Historical replay framework exists, but crisis-window quality depends on having clean long-history price data.",
            "",
            "=" * 80,
            "DIGITAL TWIN CONCLUSION",
            "=" * 80,
            f"AURUM Digital Twin Status: {final_summary['overall_digital_twin_status']}",
        ]

        txt_path.write_text("\n".join(lines), encoding="utf-8")

    def print_summary(self, final_summary: Dict[str, Any]) -> None:
        print("=" * 80)
        print("AURUM MARKET DIGITAL TWIN FINAL REPORT")
        print("=" * 80)
        print(
            f"Overall Digital Twin Status: "
            f"{final_summary['overall_digital_twin_status']}"
        )

        monte_carlo = final_summary.get("monte_carlo", {})
        worst_stress = final_summary.get("worst_stress_scenario", {})
        worst_contagion = final_summary.get("worst_contagion_source", {})
        regime = final_summary.get("regime_transition", {})

        print("-" * 80)
        print(f"Monte Carlo Survival: {monte_carlo.get('survival_status')}")
        print(f"Worst Stress Scenario: {worst_stress.get('scenario_id')}")
        print(f"Worst Stress Impact: {worst_stress.get('portfolio_impact')}")
        print(f"Worst Contagion Source: {worst_contagion.get('source_asset')}")
        print(f"Worst Contagion Impact: {worst_contagion.get('total_portfolio_impact')}")
        print(f"Regime Risk Level: {regime.get('regime_risk_level')}")


def main() -> None:
    generator = DigitalTwinReportGenerator()
    summary = generator.run()
    generator.print_summary(summary)


if __name__ == "__main__":
    main()