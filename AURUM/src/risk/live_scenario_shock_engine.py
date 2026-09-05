from pathlib import Path
import pandas as pd


class LiveScenarioShockEngine:
    def __init__(
        self,
        meta_weights_path="data/optimization/meta_strategy_weights.csv",
        live_overlay_path="data/live/live_allocation_overlay.csv",
        output_csv_path="data/risk/live_scenario_shock_results.csv",
        output_report_path="results/risk/live_scenario_shock_report.txt",
    ):
        self.meta_weights_path = Path(meta_weights_path)
        self.live_overlay_path = Path(live_overlay_path)
        self.output_csv_path = Path(output_csv_path)
        self.output_report_path = Path(output_report_path)

        self.scenarios = {
            "equity_gap_down": {
                "rolling_min_variance": -0.025,
                "dynamic_allocation": -0.020,
                "regime_aware": -0.015,
                "black_litterman": -0.060,
                "hrp": -0.025,
                "bayesian_robust": -0.030,
            },
            "crypto_crash": {
                "rolling_min_variance": -0.005,
                "dynamic_allocation": -0.010,
                "regime_aware": -0.005,
                "black_litterman": -0.040,
                "hrp": -0.012,
                "bayesian_robust": -0.020,
            },
            "rates_shock": {
                "rolling_min_variance": -0.020,
                "dynamic_allocation": -0.015,
                "regime_aware": -0.010,
                "black_litterman": -0.010,
                "hrp": -0.035,
                "bayesian_robust": -0.015,
            },
            "risk_on_rally": {
                "rolling_min_variance": 0.015,
                "dynamic_allocation": 0.020,
                "regime_aware": 0.012,
                "black_litterman": 0.055,
                "hrp": 0.018,
                "bayesian_robust": 0.025,
            },
            "volatility_spike": {
                "rolling_min_variance": -0.018,
                "dynamic_allocation": -0.012,
                "regime_aware": -0.008,
                "black_litterman": -0.045,
                "hrp": -0.020,
                "bayesian_robust": -0.022,
            },
        }

    def run(self):
        base_weights = pd.read_csv(self.meta_weights_path)
        live_weights = pd.read_csv(self.live_overlay_path)

        weight_col = "live_weight" if "live_weight" in live_weights.columns else "meta_weight"

        base_map = dict(zip(base_weights["strategy"], base_weights["meta_weight"]))
        live_map = dict(zip(live_weights["strategy"], live_weights[weight_col]))

        rows = []

        for scenario, shock_map in self.scenarios.items():
            base_impact = 0.0
            live_impact = 0.0

            worst_strategy = "none_positive_scenario"
            worst_contribution = 0.0

            for strategy, shock_return in shock_map.items():
                base_weight = base_map.get(strategy, 0.0)
                live_weight = live_map.get(strategy, 0.0)

                base_contribution = base_weight * shock_return
                live_contribution = live_weight * shock_return

                base_impact += base_contribution
                live_impact += live_contribution

                if live_contribution < worst_contribution:
                    worst_contribution = live_contribution
                    worst_strategy = strategy

            rows.append({
                "scenario": scenario,
                "base_portfolio_impact": base_impact,
                "live_portfolio_impact": live_impact,
                "overlay_delta": live_impact - base_impact,
                "worst_strategy": worst_strategy,
                "worst_strategy_contribution": worst_contribution,
            })

        results = pd.DataFrame(rows)

        worst_case = results.sort_values(
            "live_portfolio_impact",
            ascending=True,
        ).iloc[0]

        best_case = results.sort_values(
            "live_portfolio_impact",
            ascending=False,
        ).iloc[0]

        self.output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_report_path.parent.mkdir(parents=True, exist_ok=True)

        results.to_csv(self.output_csv_path, index=False)

        lines = []

        lines.append("AURUM LIVE SCENARIO SHOCK REPORT")
        lines.append("=" * 70)
        lines.append("")

        lines.append("SCENARIO RESULTS")
        lines.append("-" * 70)

        for _, row in results.iterrows():
            lines.append(
                f"{row['scenario']:<22} | "
                f"Base Impact: {row['base_portfolio_impact']:.2%} | "
                f"Live Impact: {row['live_portfolio_impact']:.2%} | "
                f"Overlay Delta: {row['overlay_delta']:+.2%} | "
                f"Worst Sleeve: {row['worst_strategy']}"
            )

        lines.append("")
        lines.append("WORST LIVE SCENARIO")
        lines.append("-" * 70)
        lines.append(
            f"{worst_case['scenario']} produces the largest estimated "
            f"live portfolio impact of {worst_case['live_portfolio_impact']:.2%}."
        )

        lines.append("")
        lines.append("BEST LIVE SCENARIO")
        lines.append("-" * 70)
        lines.append(
            f"{best_case['scenario']} produces the strongest estimated "
            f"live portfolio impact of {best_case['live_portfolio_impact']:.2%}."
        )

        lines.append("")
        lines.append("RISK INTERPRETATION")
        lines.append("-" * 70)

        if worst_case["live_portfolio_impact"] < -0.03:
            lines.append(
                "The current live overlay remains vulnerable to a severe "
                "risk-off or volatility shock. Defensive rebalancing should "
                "be considered if live stress indicators rise."
            )
        else:
            lines.append(
                "The current live overlay shows controlled downside under "
                "defined shock scenarios."
            )

        report = "\n".join(lines)

        with open(self.output_report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print("LIVE SCENARIO SHOCK ENGINE COMPLETE")
        print("=" * 70)
        print(report)
        print()
        print(f"Saved scenario results: {self.output_csv_path}")
        print(f"Saved scenario report: {self.output_report_path}")

        return results, report


if __name__ == "__main__":
    engine = LiveScenarioShockEngine()
    engine.run()