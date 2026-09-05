import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class VolatilityVisualizer:

    def __init__(self):

        self.input_path = Path("data/forecasting")
        self.output_path = Path("results/figures")

    def load_forecasts(self):

        df = pd.read_csv(
            self.input_path / "volatility_forecasts.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def plot_asset_volatility(self, df, asset):

        plt.figure(figsize=(12, 6))

        plt.plot(df["Date"], df[f"{asset}_rolling_vol_20"], label="Rolling Vol 20")
        plt.plot(df["Date"], df[f"{asset}_rolling_vol_60"], label="Rolling Vol 60")
        plt.plot(df["Date"], df[f"{asset}_ewma_vol"], label="EWMA Vol")

        plt.title(f"{asset} Volatility Forecasts", fontsize=16)
        plt.xlabel("Date")
        plt.ylabel("Volatility")
        plt.legend()
        plt.grid(True)

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / f"{asset}_volatility_forecast.png"

        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        print(f"Saved figure: {output_file}")

        plt.show()

    def run(self):

        df = self.load_forecasts()

        for asset in ["SPY", "QQQ", "TLT", "BTC-USD", "VIX"]:

            self.plot_asset_volatility(df, asset)


if __name__ == "__main__":

    visualizer = VolatilityVisualizer()

    visualizer.run()
