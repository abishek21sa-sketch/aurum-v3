import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class FactorExposureVisualizer:

    def __init__(self):
        self.input_path = Path("data/analytics")
        self.output_path = Path("results/figures")

    def load_data(self):
        return pd.read_csv(
            self.input_path / "portfolio_factor_exposure.csv"
        )

    def plot_beta_contribution(self, df):
        df = df.sort_values(
            "weighted_beta_contribution",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            df["asset"],
            df["weighted_beta_contribution"]
        )

        plt.title("Portfolio Beta Contribution by Asset", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Weighted Beta Contribution")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "portfolio_beta_contribution.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Saved beta contribution figure: {output_file}")

        plt.show()

    def run(self):
        df = self.load_data()
        self.plot_beta_contribution(df)


if __name__ == "__main__":
    visualizer = FactorExposureVisualizer()
    visualizer.run()
