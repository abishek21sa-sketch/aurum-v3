import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class ConfidenceAdjustedVisualizer:

    def __init__(self):
        self.input_path = Path("data/optimization")
        self.output_path = Path("results/figures")

    def load_weights(self):
        return pd.read_csv(
            self.input_path / "confidence_adjusted_weights.csv"
        )

    def plot_weights(self, weights):
        weights = weights.sort_values("weight", ascending=False)

        plt.figure(figsize=(10, 6))
        plt.bar(weights["asset"], weights["weight"])

        plt.title("Confidence-Adjusted Allocation Weights", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Portfolio Weight")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "confidence_adjusted_weights.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Saved figure: {output_file}")

        plt.show()

    def run(self):
        weights = self.load_weights()
        self.plot_weights(weights)


if __name__ == "__main__":
    visualizer = ConfidenceAdjustedVisualizer()
    visualizer.run()
