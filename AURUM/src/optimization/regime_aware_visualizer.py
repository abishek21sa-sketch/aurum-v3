import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RegimeAwareVisualizer:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/figures")

    def load_weights(self):

        return pd.read_csv(
            self.optimization_path / "regime_aware_weights.csv"
        )

    def plot_regime_weights(self, weights):

        regimes = sorted(weights["regime"].unique())

        self.output_path.mkdir(parents=True, exist_ok=True)

        for regime in regimes:

            regime_weights = weights[
                weights["regime"] == regime
            ].sort_values(
                "weight",
                ascending=False
            )

            plt.figure(figsize=(10, 6))

            plt.bar(
                regime_weights["asset"],
                regime_weights["weight"]
            )

            plt.title(
                f"Regime-Aware Portfolio Weights: {regime}",
                fontsize=16
            )

            plt.xlabel("Asset")
            plt.ylabel("Portfolio Weight")
            plt.xticks(rotation=45)
            plt.grid(axis="y")

            output_file = (
                self.output_path /
                f"regime_aware_weights_{regime}.png"
            )

            plt.savefig(
                output_file,
                dpi=300,
                bbox_inches="tight"
            )

            print(f"Saved figure: {output_file}")

            plt.show()

    def run(self):

        weights = self.load_weights()

        self.plot_regime_weights(weights)


if __name__ == "__main__":

    visualizer = RegimeAwareVisualizer()

    visualizer.run()
