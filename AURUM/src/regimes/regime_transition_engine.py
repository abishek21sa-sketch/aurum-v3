import pandas as pd
import numpy as np
from pathlib import Path


class RegimeTransitionEngine:

    def __init__(self):

        self.regime_path = Path("data/regimes")
        self.output_path = Path("data/regimes")

    def load_regimes(self):

        df = pd.read_csv(
            self.regime_path / "market_regimes.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df.sort_values("Date")

    def compute_transition_matrix(self, df):

        regimes = sorted(df["regime"].unique())

        transition_counts = pd.DataFrame(
            0,
            index=regimes,
            columns=regimes
        )

        regime_series = df["regime"].values

        for i in range(len(regime_series) - 1):

            current_regime = regime_series[i]
            next_regime = regime_series[i + 1]

            transition_counts.loc[
                current_regime,
                next_regime
            ] += 1

        transition_matrix = transition_counts.div(
            transition_counts.sum(axis=1),
            axis=0
        ).fillna(0)

        return transition_counts, transition_matrix

    def compute_regime_persistence(self, transition_matrix):

        records = []

        for regime in transition_matrix.index:

            records.append(
                {
                    "regime": regime,
                    "persistence_probability": transition_matrix.loc[
                        regime,
                        regime
                    ]
                }
            )

        persistence_df = pd.DataFrame(records)

        return persistence_df

    def save_outputs(
        self,
        transition_counts,
        transition_matrix,
        persistence_df
    ):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        counts_file = self.output_path / "regime_transition_counts.csv"
        matrix_file = self.output_path / "regime_transition_matrix.csv"
        persistence_file = self.output_path / "regime_persistence.csv"

        transition_counts.to_csv(counts_file)
        transition_matrix.to_csv(matrix_file)
        persistence_df.to_csv(persistence_file, index=False)

        print("\nREGIME TRANSITION COUNTS")
        print("=" * 60)
        print(transition_counts.to_string())

        print("\nREGIME TRANSITION MATRIX")
        print("=" * 60)
        print(transition_matrix.round(4).to_string())

        print("\nREGIME PERSISTENCE")
        print("=" * 60)
        print(persistence_df.to_string(index=False))

        print(f"\nSaved transition counts: {counts_file}")
        print(f"Saved transition matrix: {matrix_file}")
        print(f"Saved persistence: {persistence_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("REGIME TRANSITION ENGINE")
        print("=" * 60)

        df = self.load_regimes()

        transition_counts, transition_matrix = (
            self.compute_transition_matrix(df)
        )

        persistence_df = self.compute_regime_persistence(
            transition_matrix
        )

        self.save_outputs(
            transition_counts,
            transition_matrix,
            persistence_df
        )


if __name__ == "__main__":

    engine = RegimeTransitionEngine()

    engine.run_pipeline()
