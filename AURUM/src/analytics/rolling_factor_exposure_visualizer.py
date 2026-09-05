import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RollingFactorExposureVisualizer:

    def __init__(self):
        self.input_path = Path("data/analytics")
        self.output_path = Path("results/figures")

    def load_data(self):
        df = pd.read_csv(
            self.input_path / "rolling_factor_exposure.csv"
        )
        df["Date"] = pd.to_datetime(df["Date"])
        return df

    def plot_rolling_beta(self, df):
        plt.figure(figsize=(12, 6))

        plt.plot(df["Date"], df["portfolio_beta_to_spy"], label="Daily Beta")
        plt.plot(df["Date"], df["rolling_beta_20"], label="20-Day Rolling Beta")
        plt.plot(df["Date"], df["rolling_beta_60"], label="60-Day Rolling Beta")

        plt.title("Rolling Portfolio Beta to SPY", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Beta to SPY")
        plt.legend()
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "rolling_portfolio_beta_to_spy.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Saved rolling beta figure: {output_file}")

        plt.show()

    def run(self):
        df = self.load_data()
        self.plot_rolling_beta(df)


if __name__ == "__main__":
    visualizer = RollingFactorExposureVisualizer()
    visualizer.run()
