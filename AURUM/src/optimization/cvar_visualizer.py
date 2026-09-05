import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class CVaRVisualizer:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/figures")

    def load_weights(self):

        return pd.read_csv(
            self.optimization_path / "cvar_weights.csv"
        )

    def plot_weights(self, weights):

        weights = weights.sort_values(
            "weight",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            weights["asset"],
            weights["weight"]
        )

        plt.title("CVaR Optimized Portfolio Weights", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Portfolio Weight")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "cvar_portfolio_weights.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved figure: {output_file}")

        plt.show()

    def run(self):

        weights = self.load_weights()

        self.plot_weights(weights)


if __name__ == "__main__":

    visualizer = CVaRVisualizer()

    visualizer.run()
