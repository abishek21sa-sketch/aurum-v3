import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class PortfolioAttributionVisualizer:

    def __init__(self):

        self.input_path = Path("data/analytics")
        self.output_path = Path("results/figures")

    def load_data(self):

        asset_attr = pd.read_csv(
            self.input_path / "asset_return_attribution.csv"
        )

        regime_attr = pd.read_csv(
            self.input_path / "regime_return_attribution.csv"
        )

        return asset_attr, regime_attr

    def plot_asset_attribution(self, asset_attr):

        asset_attr = asset_attr.sort_values(
            "annualized_return_contribution",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            asset_attr["asset"],
            asset_attr["annualized_return_contribution"]
        )

        plt.title("Annualized Return Contribution by Asset", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Annualized Return Contribution")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "asset_return_attribution.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved asset attribution figure: {output_file}")

        plt.show()

    def plot_regime_attribution(self, regime_attr):

        regime_attr = regime_attr.sort_values(
            "total_return",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            regime_attr["regime"],
            regime_attr["total_return"]
        )

        plt.title("Total Return Contribution by Regime", fontsize=16)
        plt.xlabel("Regime")
        plt.ylabel("Total Return Contribution")
        plt.xticks(rotation=30)
        plt.grid(axis="y")

        output_file = self.output_path / "regime_return_attribution.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved regime attribution figure: {output_file}")

        plt.show()

    def run(self):

        asset_attr, regime_attr = self.load_data()

        self.plot_asset_attribution(asset_attr)

        self.plot_regime_attribution(regime_attr)


if __name__ == "__main__":

    visualizer = PortfolioAttributionVisualizer()

    visualizer.run()
