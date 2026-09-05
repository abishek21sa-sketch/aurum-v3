import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class LiveAllocationVisualizer:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.regime_path = Path("data/regimes")
        self.output_path = Path("results/figures")

    def load_inputs(self):

        weights = pd.read_csv(
            self.optimization_path / "probabilistic_regime_weights.csv"
        )

        forecast = pd.read_csv(
            self.regime_path / "next_regime_forecast.csv"
        )

        return weights, forecast

    def plot_allocation(self, weights):

        weights = weights.sort_values(
            "weight",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            weights["asset"],
            weights["weight"]
        )

        plt.title("Live Probabilistic Allocation Recommendation", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Portfolio Weight")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "live_allocation_weights.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved allocation figure: {output_file}")

        plt.show()

    def plot_regime_forecast(self, forecast):

        forecast = forecast.sort_values(
            "probability",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            forecast["next_regime"],
            forecast["probability"]
        )

        plt.title("Next-Regime Probability Forecast", fontsize=16)
        plt.xlabel("Next Regime")
        plt.ylabel("Probability")
        plt.xticks(rotation=30)
        plt.grid(axis="y")

        output_file = self.output_path / "next_regime_probability_forecast.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved regime forecast figure: {output_file}")

        plt.show()

    def run(self):

        weights, forecast = self.load_inputs()

        self.plot_allocation(weights)

        self.plot_regime_forecast(forecast)


if __name__ == "__main__":

    visualizer = LiveAllocationVisualizer()

    visualizer.run()
