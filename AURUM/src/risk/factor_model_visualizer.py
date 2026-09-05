import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class FactorModelVisualizer:

    def __init__(self):

        self.input_path = Path("data/risk")
        self.output_path = Path("results/figures")

    def load_exposures(self):

        return pd.read_csv(
            self.input_path / "factor_exposures.csv"
        )

    def plot_betas(self, exposures):

        exposures = exposures.sort_values(
            "beta",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            exposures["asset"],
            exposures["beta"]
        )

        plt.title("Asset Beta Exposure to SPY", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Beta")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "factor_beta_exposures.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved beta figure: {output_file}")

        plt.show()

    def plot_correlations(self, exposures):

        exposures = exposures.sort_values(
            "correlation",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            exposures["asset"],
            exposures["correlation"]
        )

        plt.title("Asset Correlation with SPY", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Correlation")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        output_file = self.output_path / "factor_correlation_exposures.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved correlation figure: {output_file}")

        plt.show()

    def run(self):

        exposures = self.load_exposures()

        self.plot_betas(exposures)

        self.plot_correlations(exposures)


if __name__ == "__main__":

    visualizer = FactorModelVisualizer()

    visualizer.run()
