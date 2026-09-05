import pandas as pd
import numpy as np
from pathlib import Path


class MonteCarloRegimeSimulator:

    def __init__(self):
        self.regime_path = Path("data/regimes")
        self.backtest_path = Path("data/backtesting")
        self.output_path = Path("data/forecasting")

    def load_inputs(self):
        transition_matrix = pd.read_csv(
            self.regime_path / "regime_transition_matrix.csv",
            index_col=0
        )

        backtest = pd.read_csv(
            self.backtest_path / "dynamic_allocation_backtest.csv"
        )

        return transition_matrix, backtest

    def estimate_regime_return_stats(self, backtest):
        stats = (
            backtest
            .groupby("regime")["portfolio_return"]
            .agg(["mean", "std"])
        )

        return stats

    def simulate_paths(
        self,
        transition_matrix,
        regime_stats,
        n_paths=1000,
        horizon_days=60
    ):
        regimes = list(transition_matrix.index)
        current_regime = regimes[0]

        paths = []

        for path_id in range(n_paths):
            regime = current_regime
            cumulative_return = 0.0

            for day in range(horizon_days):
                probabilities = transition_matrix.loc[regime].values

                next_regime = np.random.choice(
                    regimes,
                    p=probabilities
                )

                mean_return = regime_stats.loc[next_regime, "mean"]
                std_return = regime_stats.loc[next_regime, "std"]

                simulated_return = np.random.normal(
                    mean_return,
                    std_return
                )

                cumulative_return = (
                    (1 + cumulative_return)
                    * (1 + simulated_return)
                    - 1
                )

                paths.append(
                    {
                        "path_id": path_id,
                        "day": day + 1,
                        "regime": next_regime,
                        "simulated_return": simulated_return,
                        "cumulative_return": cumulative_return
                    }
                )

                regime = next_regime

        return pd.DataFrame(paths)

    def summarize_paths(self, paths):
        terminal = (
            paths
            .groupby("path_id")
            .tail(1)
            .copy()
        )

        summary = pd.DataFrame({
            "metric": [
                "mean_terminal_return",
                "median_terminal_return",
                "p05_terminal_return",
                "p95_terminal_return",
                "probability_loss"
            ],
            "value": [
                terminal["cumulative_return"].mean(),
                terminal["cumulative_return"].median(),
                terminal["cumulative_return"].quantile(0.05),
                terminal["cumulative_return"].quantile(0.95),
                (terminal["cumulative_return"] < 0).mean()
            ]
        })

        return summary

    def save_outputs(self, paths, summary):
        self.output_path.mkdir(parents=True, exist_ok=True)

        paths_file = self.output_path / "monte_carlo_regime_paths.csv"
        summary_file = self.output_path / "monte_carlo_regime_summary.csv"

        paths.to_csv(paths_file, index=False)
        summary.to_csv(summary_file, index=False)

        print("\nMONTE CARLO REGIME SIMULATION SUMMARY")
        print("=" * 60)
        print(summary.to_string(index=False))

        print(f"\nSaved paths: {paths_file}")
        print(f"Saved summary: {summary_file}")

    def run_pipeline(self):
        print("=" * 60)
        print("MONTE CARLO REGIME SIMULATOR")
        print("=" * 60)

        transition_matrix, backtest = self.load_inputs()
        regime_stats = self.estimate_regime_return_stats(backtest)

        paths = self.simulate_paths(
            transition_matrix,
            regime_stats,
            n_paths=1000,
            horizon_days=60
        )

        summary = self.summarize_paths(paths)

        self.save_outputs(paths, summary)


if __name__ == "__main__":
    simulator = MonteCarloRegimeSimulator()
    simulator.run_pipeline()
