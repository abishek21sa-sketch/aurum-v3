import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class StressTestVisualizer:

    def __init__(self):

        self.input_path = Path("data/risk")
        self.output_path = Path("results/figures")

    def load_summary(self):

        return pd.read_csv(
            self.input_path / "stress_test_summary.csv"
        )

    def plot_heatmap_style(self, summary_df):

        pivot = summary_df.pivot(
            index="portfolio",
            columns="scenario",
            values="scenario_return"
        )

        plt.figure(figsize=(10, 6))

        plt.imshow(
            pivot,
            aspect="auto"
        )

        plt.colorbar(label="Scenario Return")

        plt.xticks(
            range(len(pivot.columns)),
            pivot.columns,
            rotation=20
        )

        plt.yticks(
            range(len(pivot.index)),
            pivot.index
        )

        plt.title(
            "Stress Test Scenario Returns",
            fontsize=16
        )

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "stress_test_heatmap.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved figure: {output_file}")

        plt.show()

    def plot_scenario_bars(self, summary_df):

        scenarios = summary_df["scenario"].unique()

        for scenario in scenarios:

            subset = summary_df[
                summary_df["scenario"] == scenario
            ]

            plt.figure(figsize=(8, 5))

            plt.bar(
                subset["portfolio"],
                subset["scenario_return"]
            )

            plt.title(
                f"Portfolio Returns under {scenario}",
                fontsize=15
            )

            plt.xlabel("Portfolio")
            plt.ylabel("Scenario Return")

            plt.grid(axis="y")

            output_file = (
                self.output_path /
                f"{scenario}_portfolio_comparison.png"
            )

            plt.savefig(
                output_file,
                dpi=300,
                bbox_inches="tight"
            )

            print(f"Saved figure: {output_file}")

            plt.show()

    def run(self):

        summary_df = self.load_summary()

        self.plot_heatmap_style(summary_df)

        self.plot_scenario_bars(summary_df)


if __name__ == "__main__":

    visualizer = StressTestVisualizer()

    visualizer.run()
