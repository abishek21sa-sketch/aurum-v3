import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RiskContributionVisualizer:

    def __init__(self):

        self.input_path = Path("results/reports")
        self.output_path = Path("results/figures")

    def load_risk_report(self):

        return pd.read_csv(
            self.input_path / "risk_contribution_report.csv"
        )

    def plot_risk_contribution(self, risk_df):

        risk_df = risk_df.sort_values(
            "percent_risk_contribution",
            ascending=False
        )

        plt.figure(figsize=(10, 6))

        plt.bar(
            risk_df["asset"],
            risk_df["percent_risk_contribution"]
        )

        plt.title("Portfolio Risk Contribution by Asset", fontsize=16)
        plt.xlabel("Asset")
        plt.ylabel("Percent Risk Contribution")
        plt.xticks(rotation=45)
        plt.grid(axis="y")

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "risk_contribution_by_asset.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved figure: {output_file}")

        plt.show()

    def run(self):

        risk_df = self.load_risk_report()

        self.plot_risk_contribution(risk_df)


if __name__ == "__main__":

    visualizer = RiskContributionVisualizer()

    visualizer.run()
