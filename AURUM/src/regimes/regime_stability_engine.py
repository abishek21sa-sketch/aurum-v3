import pandas as pd
import numpy as np
from pathlib import Path


class RegimeStabilityEngine:

    def __init__(self):

        self.regime_path = Path("data/regimes")
        self.output_path = Path("data/regimes")

    def load_regimes(self):

        df = pd.read_csv(
            self.regime_path / "market_regimes.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df.sort_values("Date")

    def compute_entropy(self, probabilities):

        probabilities = probabilities[probabilities > 0]

        return -np.sum(
            probabilities * np.log(probabilities)
        )

    def compute_rolling_stability(
        self,
        df,
        window=60
    ):

        records = []

        for i in range(window, len(df)):

            sample = df.iloc[i - window:i]

            regime_counts = (
                sample["regime"]
                .value_counts(normalize=True)
            )

            entropy = self.compute_entropy(
                regime_counts.values
            )

            dominant_regime = regime_counts.idxmax()
            dominant_probability = regime_counts.max()

            instability_score = entropy * (
                1 - dominant_probability
            )

            records.append(
                {
                    "Date": df.iloc[i]["Date"],
                    "dominant_regime": dominant_regime,
                    "dominant_regime_probability": dominant_probability,
                    "transition_entropy": entropy,
                    "instability_score": instability_score
                }
            )

        return pd.DataFrame(records)

    def save_outputs(self, stability_df):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "regime_stability.csv"

        stability_df.to_csv(output_file, index=False)

        print("\nREGIME STABILITY ANALYSIS")
        print("=" * 60)

        print(stability_df.tail().to_string(index=False))

        print(f"\nSaved stability results: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("REGIME STABILITY ENGINE")
        print("=" * 60)

        df = self.load_regimes()

        stability_df = self.compute_rolling_stability(
            df,
            window=60
        )

        self.save_outputs(stability_df)


if __name__ == "__main__":

    engine = RegimeStabilityEngine()

    engine.run_pipeline()
