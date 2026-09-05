import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RegimeStabilityVisualizer:

    def __init__(self):

        self.input_path = Path("data/regimes")
        self.output_path = Path("results/figures")

    def load_stability(self):

        df = pd.read_csv(
            self.input_path / "regime_stability.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def plot_instability_score(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(df["Date"], df["instability_score"])

        plt.title("Rolling Regime Instability Score", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Instability Score")
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "regime_instability_score.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved instability figure: {output_file}")

        plt.show()

    def plot_entropy(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(df["Date"], df["transition_entropy"])

        plt.title("Rolling Regime Entropy", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Entropy")
        plt.grid(True)

        output_file = self.output_path / "regime_transition_entropy.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved entropy figure: {output_file}")

        plt.show()

    def plot_dominant_probability(self, df):

        plt.figure(figsize=(12, 6))

        plt.plot(df["Date"], df["dominant_regime_probability"])

        plt.title("Rolling Dominant Regime Probability", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Dominant Regime Probability")
        plt.grid(True)

        output_file = self.output_path / "dominant_regime_probability.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved dominance figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_stability()

        self.plot_instability_score(df)
        self.plot_entropy(df)
        self.plot_dominant_probability(df)


if __name__ == "__main__":

    visualizer = RegimeStabilityVisualizer()

    visualizer.run()
