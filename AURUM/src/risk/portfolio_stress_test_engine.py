import pandas as pd
from pathlib import Path


class PortfolioStressTestEngine:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("data/risk")

    def load_allocations(self):

        allocations = {
            "probabilistic_regime": pd.read_csv(
                self.optimization_path / "probabilistic_regime_weights.csv"
            ),
            "confidence_adjusted": pd.read_csv(
                self.optimization_path / "confidence_adjusted_weights.csv"
            )
        }

        return allocations

    def define_stress_scenarios(self):

        return {
            "equity_crash": {
                "SPY": -0.12,
                "QQQ": -0.16,
                "DIA": -0.10,
                "TLT": 0.04,
                "GLD": 0.03,
                "VIX": 0.45,
                "BTC-USD": -0.20,
                "ETH-USD": -0.25
            },
            "volatility_spike": {
                "SPY": -0.06,
                "QQQ": -0.08,
                "DIA": -0.05,
                "TLT": 0.02,
                "GLD": 0.02,
                "VIX": 0.35,
                "BTC-USD": -0.12,
                "ETH-USD": -0.15
            },
            "rates_shock": {
                "SPY": -0.04,
                "QQQ": -0.06,
                "DIA": -0.03,
                "TLT": -0.10,
                "GLD": -0.02,
                "VIX": 0.12,
                "BTC-USD": -0.08,
                "ETH-USD": -0.10
            },
            "crypto_collapse": {
                "SPY": -0.02,
                "QQQ": -0.03,
                "DIA": -0.01,
                "TLT": 0.01,
                "GLD": 0.02,
                "VIX": 0.08,
                "BTC-USD": -0.35,
                "ETH-USD": -0.45
            },
            "risk_on_rally": {
                "SPY": 0.06,
                "QQQ": 0.09,
                "DIA": 0.04,
                "TLT": -0.03,
                "GLD": -0.01,
                "VIX": -0.20,
                "BTC-USD": 0.15,
                "ETH-USD": 0.20
            }
        }

    def compute_stress_return(self, weights, scenario):

        weights = weights.set_index("asset")["weight"]

        scenario_series = pd.Series(scenario)

        aligned_weights = weights.reindex(
            scenario_series.index
        ).fillna(0)

        contribution = aligned_weights * scenario_series

        stress_return = contribution.sum()

        return stress_return, contribution

    def run_stress_tests(self, allocations, scenarios):

        summary_records = []
        contribution_records = []

        for allocation_name, weights in allocations.items():

            for scenario_name, scenario in scenarios.items():

                stress_return, contribution = self.compute_stress_return(
                    weights,
                    scenario
                )

                summary_records.append(
                    {
                        "allocation": allocation_name,
                        "scenario": scenario_name,
                        "stress_return": stress_return
                    }
                )

                for asset, value in contribution.items():

                    contribution_records.append(
                        {
                            "allocation": allocation_name,
                            "scenario": scenario_name,
                            "asset": asset,
                            "shock": scenario[asset],
                            "contribution": value
                        }
                    )

        summary_df = pd.DataFrame(summary_records)
        contribution_df = pd.DataFrame(contribution_records)

        return summary_df, contribution_df

    def save_outputs(self, summary_df, contribution_df):

        self.output_path.mkdir(parents=True, exist_ok=True)

        summary_file = self.output_path / "portfolio_stress_summary.csv"
        contribution_file = self.output_path / "portfolio_stress_contributions.csv"

        summary_df.to_csv(summary_file, index=False)
        contribution_df.to_csv(contribution_file, index=False)

        print("\nPORTFOLIO STRESS TEST SUMMARY")
        print("=" * 60)

        print(
            summary_df.pivot(
                index="allocation",
                columns="scenario",
                values="stress_return"
            ).to_string()
        )

        print(f"\nSaved summary: {summary_file}")
        print(f"Saved contributions: {contribution_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("PORTFOLIO STRESS TEST ENGINE")
        print("=" * 60)

        allocations = self.load_allocations()
        scenarios = self.define_stress_scenarios()

        summary_df, contribution_df = self.run_stress_tests(
            allocations,
            scenarios
        )

        self.save_outputs(
            summary_df,
            contribution_df
        )


if __name__ == "__main__":

    engine = PortfolioStressTestEngine()

    engine.run_pipeline()
