import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class SignalVisualizer:

    def __init__(self):

        self.signal_path = Path("data/signals")
        self.output_path = Path("results/figures")

    def load_signals(self):

        df = pd.read_csv(
            self.signal_path / "market_signals.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def plot_signal_strength(self, df):

        plt.figure(figsize=(16, 7))

        plt.plot(
            df["Date"],
            df["signal_strength"],
            linewidth=1.5
        )

        plt.title("Market Signal Strength Over Time", fontsize=18)
        plt.xlabel("Date")
        plt.ylabel("Signal Strength")
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "market_signal_strength.png"

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved figure: {output_file}")

        plt.show()

    def plot_signal_distribution(self, df):

        counts = df["risk_signal"].value_counts()

        plt.figure(figsize=(10, 6))

        counts.plot(kind="bar")

        plt.title("Risk Signal Distribution", fontsize=16)
        plt.xlabel("Risk Signal")
        plt.ylabel("Count")
        plt.grid(axis="y")

        output_file = self.output_path / "risk_signal_distribution.png"

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"Saved figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_signals()

        self.plot_signal_strength(df)

        self.plot_signal_distribution(df)


if __name__ == "__main__":

    visualizer = SignalVisualizer()

    visualizer.run()
