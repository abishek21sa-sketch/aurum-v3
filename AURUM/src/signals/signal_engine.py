import pandas as pd
from pathlib import Path


class QuantSignalEngine:

    def __init__(self):

        self.regime_path = Path("data/regimes")
        self.output_path = Path("data/signals")

    def load_regime_data(self):

        df = pd.read_csv(
            self.regime_path / "market_regimes.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def generate_risk_signal(self, row):

        if row["regime_label"] == "shock":
            return "risk_off"

        if row["regime_label"] == "stress":
            return "defensive"

        if (
            row["regime_label"] == "normal"
            and row["market_mean_return"] > 0
        ):
            return "risk_on"

        return "neutral"

    def generate_signal_strength(self, row):

        strength = (
            abs(row["market_mean_return"])
            + row["market_volatility"]
            + row["cross_asset_dispersion"]
        )

        return strength

    def build_signals(self, df):

        df = df.copy()

        df["risk_signal"] = df.apply(
            self.generate_risk_signal,
            axis=1
        )

        df["signal_strength"] = df.apply(
            self.generate_signal_strength,
            axis=1
        )

        return df

    def save_outputs(self, signal_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = self.output_path / "market_signals.csv"

        signal_df.to_csv(output_file, index=False)

        print(f"Saved signal output: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("QUANT SIGNAL ENGINE")
        print("=" * 60)

        df = self.load_regime_data()

        signal_df = self.build_signals(df)

        self.save_outputs(signal_df)

        print("\nLATEST SIGNALS")
        print(
            signal_df[
                [
                    "Date",
                    "regime_label",
                    "market_mean_return",
                    "market_volatility",
                    "cross_asset_dispersion",
                    "risk_signal",
                    "signal_strength",
                ]
            ].tail(20)
        )


if __name__ == "__main__":

    engine = QuantSignalEngine()

    engine.run_pipeline()
