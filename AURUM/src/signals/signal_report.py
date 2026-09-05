import pandas as pd
from pathlib import Path


class SignalReport:

    def __init__(self):

        self.signal_path = Path("data/signals")
        self.output_path = Path("results/reports")

    def load_signals(self):

        df = pd.read_csv(
            self.signal_path / "market_signals.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def build_summary(self, df):

        latest = df.iloc[-1]

        signal_counts = (
            df["risk_signal"]
            .value_counts()
            .reset_index()
        )

        signal_counts.columns = [
            "risk_signal",
            "count"
        ]

        regime_counts = (
            df["regime_label"]
            .value_counts()
            .reset_index()
        )

        regime_counts.columns = [
            "regime_label",
            "count"
        ]

        summary_text = f"""
MARKET SIGNAL REPORT
====================

Latest Date:
{latest["Date"]}

Latest Regime:
{latest["regime_label"]}

Latest Risk Signal:
{latest["risk_signal"]}

Latest Market Mean Return:
{latest["market_mean_return"]:.6f}

Latest Market Volatility:
{latest["market_volatility"]:.6f}

Latest Cross-Asset Dispersion:
{latest["cross_asset_dispersion"]:.6f}

Latest Signal Strength:
{latest["signal_strength"]:.6f}


REGIME DISTRIBUTION
===================
{regime_counts.to_string(index=False)}


RISK SIGNAL DISTRIBUTION
========================
{signal_counts.to_string(index=False)}
"""

        return summary_text

    def save_report(self, summary_text):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = self.output_path / "market_signal_report.txt"

        with open(output_file, "w") as file:
            file.write(summary_text)

        print(summary_text)
        print(f"\nSaved report: {output_file}")

    def run(self):

        df = self.load_signals()

        summary_text = self.build_summary(df)

        self.save_report(summary_text)


if __name__ == "__main__":

    report = SignalReport()

    report.run()
