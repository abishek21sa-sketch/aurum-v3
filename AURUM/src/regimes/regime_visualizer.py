import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RegimeVisualizer:

    def __init__(self):

        self.regime_path = Path(
            "data/regimes"
        )

        self.output_path = Path(
            "results/figures"
        )

    def load_regime_data(self):

        df = pd.read_csv(
            self.regime_path /
            "market_regimes.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def create_regime_plot(
        self,
        df
    ):

        plt.figure(figsize=(16, 7))

        colors = {
            "normal": "green",
            "stress": "orange",
            "shock": "red"
        }

        for label in df["regime_label"].unique():

            subset = df[
                df["regime_label"] == label
            ]

            plt.scatter(
                subset["Date"],
                subset["market_volatility"],
                label=label,
                alpha=0.7,
                s=20,
                color=colors[label]
            )

        plt.title(
            "Market Regime Detection",
            fontsize=18
        )

        plt.xlabel("Date")
        plt.ylabel("Market Volatility")

        plt.legend()

        plt.grid(True)

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "market_regime_detection.png"
        )

        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(f"\nSaved figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_regime_data()

        self.create_regime_plot(df)


if __name__ == "__main__":

    visualizer = RegimeVisualizer()

    visualizer.run()
