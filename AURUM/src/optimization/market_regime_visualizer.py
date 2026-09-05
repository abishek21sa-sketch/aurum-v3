import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class MarketRegimeVisualizer:

    def __init__(self):

        self.input_path = Path("data/regimes")
        self.output_path = Path("results/figures")

    def load_regimes(self):

        df = pd.read_csv(
            self.input_path / "market_regimes.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def plot_regime_counts(self, df):

        counts = df["regime"].value_counts()

        plt.figure(figsize=(10, 6))

        plt.bar(
            counts.index,
            counts.values
        )

        plt.title("Market Regime Counts", fontsize=16)
        plt.xlabel("Regime")
        plt.ylabel("Count")
        plt.xticks(rotation=30)
        plt.grid(axis="y")

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "market_regime_counts.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved regime count figure: {output_file}")

        plt.show()

    def plot_regime_timeline(self, df):

        regime_map = {
            "normal": 0,
            "bull": 1,
            "high_volatility": 2,
            "crisis": 3
        }

        df["regime_code"] = df["regime"].map(regime_map)

        plt.figure(figsize=(12, 6))

        plt.scatter(
            df["Date"],
            df["regime_code"],
            s=20
        )

        plt.yticks(
            list(regime_map.values()),
            list(regime_map.keys())
        )

        plt.title("Market Regime Timeline", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Regime")
        plt.grid(True)

        output_file = self.output_path / "market_regime_timeline.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved regime timeline figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_regimes()

        self.plot_regime_counts(df)

        self.plot_regime_timeline(df)


if __name__ == "__main__":

    visualizer = MarketRegimeVisualizer()

    visualizer.run()
