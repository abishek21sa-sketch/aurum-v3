from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


class FactorAttributionVisualizerV2:
    def __init__(
        self,
        attribution_path="data/analytics/factor_attribution_v2.csv",
        output_dir="results/figures",
    ):
        self.attribution_path = Path(attribution_path)
        self.output_dir = Path(output_dir)

    def load_data(self):
        df = pd.read_csv(self.attribution_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return df

    def plot_factor_correlation(self, df):
        plot_df = df.sort_values("correlation", ascending=True)

        plt.figure(figsize=(10, 6))
        plt.barh(plot_df["factor"], plot_df["correlation"])
        plt.xlabel("Correlation with Meta Strategy")
        plt.title("Meta Strategy Factor Correlation")
        plt.tight_layout()

        path = self.output_dir / "factor_correlation_v2.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path

    def plot_return_contribution(self, df):
        plot_df = df.sort_values("estimated_return_contribution", ascending=True)

        plt.figure(figsize=(10, 6))
        plt.barh(
            plot_df["factor"],
            plot_df["estimated_return_contribution"],
        )
        plt.xlabel("Estimated Annualized Return Contribution")
        plt.title("Estimated Factor Return Contribution")
        plt.tight_layout()

        path = self.output_dir / "factor_return_contribution_v2.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path

    def plot_factor_beta(self, df):
        plot_df = df.sort_values("beta", ascending=True)

        plt.figure(figsize=(10, 6))
        plt.barh(plot_df["factor"], plot_df["beta"])
        plt.xlabel("Estimated Beta")
        plt.title("Meta Strategy Factor Beta Exposure")
        plt.tight_layout()

        path = self.output_dir / "factor_beta_exposure_v2.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path

    def run(self):
        df = self.load_data()

        paths = [
            self.plot_factor_correlation(df),
            self.plot_return_contribution(df),
            self.plot_factor_beta(df),
        ]

        print("FACTOR ATTRIBUTION VISUALIZATIONS V2 COMPLETE")
        print("=" * 70)

        for path in paths:
            print(f"Saved figure: {path}")

        return paths


if __name__ == "__main__":
    visualizer = FactorAttributionVisualizerV2()
    visualizer.run()