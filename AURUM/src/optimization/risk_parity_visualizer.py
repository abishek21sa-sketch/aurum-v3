import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RiskParityVisualizer:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.output_path = Path("results/figures")

    def load_weights(self):

        return pd.read_csv(
            self.optimization_path / "risk_parity_weights.csv"
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

        plt.title("Risk Parity Portfolio Weights", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Portfolio Weight")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "risk_parity_portfolio_weights.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved weight figure: {output_file}")

        plt.show()

    def plot_risk_contributions(self, weights):

        weights = weights.sort_values(
            "risk_contribution",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            weights["asset"],
            weights["risk_contribution"]
        )

        plt.title("Risk Parity Risk Contributions", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Risk Contribution")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        output_file = (
            self.output_path /
            "risk_parity_risk_contributions.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved risk contribution figure: {output_file}")

        plt.show()

    def run(self):

        weights = self.load_weights()

        self.plot_weights(weights)

        self.plot_risk_contributions(weights)


if __name__ == "__main__":

    visualizer = RiskParityVisualizer()

    visualizer.run()
