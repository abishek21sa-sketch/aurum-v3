import pandas as pd
from pathlib import Path


class StressTestEngine:

    def __init__(self):

        self.weights_path = Path("data/optimization")
        self.output_path = Path("data/risk")

    def load_portfolios(self):

        portfolios = {
            "minimum_variance": pd.read_csv(
                self.weights_path / "min_variance_weights.csv"
            ),
            "risk_parity": pd.read_csv(
                self.weights_path / "risk_parity_weights.csv"
            ),
            "max_sharpe": pd.read_csv(
                self.weights_path / "max_sharpe_weights.csv"
            ),
            "cvar": pd.read_csv(
                self.weights_path / "cvar_weights.csv"
            )
        }

        return portfolios

    def define_scenarios(self):

        scenarios = {
            "equity_crash": {
                "SPY": -0.12,
                "QQQ": -0.16,
                "DIA": -0.10,
                "VIX": 0.45,
                "TLT": 0.04,
                "GLD": 0.03,
                "BTC-USD": -0.20,
                "ETH-USD": -0.25
            },
            "rates_shock": {
                "SPY": -0.04,
                "QQQ": -0.06,
                "DIA": -0.03,
                "VIX": 0.12,
                "TLT": -0.10,
                "GLD": -0.02,
                "BTC-USD": -0.08,
                "ETH-USD": -0.10
            },
            "crypto_crash": {
                "SPY": -0.02,
                "QQQ": -0.03,
                "DIA": -0.01,
                "VIX": 0.08,
                "TLT": 0.01,
                "GLD": 0.02,
                "BTC-USD": -0.35,
                "ETH-USD": -0.45
            },
            "risk_on_rally": {
                "SPY": 0.06,
                "QQQ": 0.09,
                "DIA": 0.04,
                "VIX": -0.20,
                "TLT": -0.03,
                "GLD": -0.01,
                "BTC-USD": 0.15,
                "ETH-USD": 0.20
            }
        }

        return scenarios

    def compute_scenario_return(self, weights, scenario):

        weights = weights.set_index("asset")["weight"]

        scenario_series = pd.Series(scenario)

        aligned_weights = weights.reindex(
            scenario_series.index
        ).fillna(0)

        contribution = aligned_weights * scenario_series

        portfolio_return = contribution.sum()

        return portfolio_return, contribution

    def run_stress_tests(self, portfolios, scenarios):

        summary_records = []
        contribution_records = []

        for portfolio_name, weights in portfolios.items():

            for scenario_name, scenario in scenarios.items():

                portfolio_return, contribution = self.compute_scenario_return(
                    weights,
                    scenario
                )

                summary_records.append(
                    {
                        "portfolio": portfolio_name,
                        "scenario": scenario_name,
                        "scenario_return": portfolio_return
                    }
                )

                for asset, contribution_value in contribution.items():

                    contribution_records.append(
                        {
                            "portfolio": portfolio_name,
                            "scenario": scenario_name,
                            "asset": asset,
                            "shock": scenario[asset],
                            "weight": weights.set_index("asset").loc[
                                asset,
                                "weight"
                            ] if asset in weights["asset"].values else 0,
                            "contribution": contribution_value
                        }
                    )

        summary_df = pd.DataFrame(summary_records)
        contribution_df = pd.DataFrame(contribution_records)

        return summary_df, contribution_df

    def save_outputs(self, summary_df, contribution_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        summary_file = self.output_path / "stress_test_summary.csv"
        contribution_file = self.output_path / "stress_test_contributions.csv"

        summary_df.to_csv(summary_file, index=False)
        contribution_df.to_csv(contribution_file, index=False)

        print("\nSTRESS TEST SUMMARY")
        print("=" * 60)

        print(
            summary_df.pivot(
                index="portfolio",
                columns="scenario",
                values="scenario_return"
            ).to_string()
        )

        print(f"\nSaved summary: {summary_file}")
        print(f"Saved contributions: {contribution_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("STRESS TEST ENGINE")
        print("=" * 60)

        portfolios = self.load_portfolios()
        scenarios = self.define_scenarios()

        summary_df, contribution_df = self.run_stress_tests(
            portfolios,
            scenarios
        )

        self.save_outputs(
            summary_df,
            contribution_df
        )


if __name__ == "__main__":

    engine = StressTestEngine()

    engine.run_pipeline()
