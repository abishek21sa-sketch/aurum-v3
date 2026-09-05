import pandas as pd
from pathlib import Path


class ProbabilisticRegimeAllocator:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.regime_path = Path("data/regimes")
        self.output_path = Path("data/optimization")

    def load_data(self):

        regime_weights = pd.read_csv(
            self.optimization_path / "regime_aware_weights.csv"
        )

        forecast = pd.read_csv(
            self.regime_path / "next_regime_forecast.csv"
        )

        return regime_weights, forecast

    def compute_probabilistic_weights(self, regime_weights, forecast):

        pivot_weights = regime_weights.pivot(
            index="regime",
            columns="asset",
            values="weight"
        )

        probability_map = forecast.set_index(
            "next_regime"
        )["probability"]

        weighted_rows = []

        for regime, probability in probability_map.items():

            if regime in pivot_weights.index:

                weighted_rows.append(
                    pivot_weights.loc[regime] * probability
                )

        probabilistic_weights = pd.concat(
            weighted_rows,
            axis=1
        ).sum(axis=1)

        probabilistic_weights = (
            probabilistic_weights /
            probabilistic_weights.sum()
        )

        weights_df = probabilistic_weights.reset_index()

        weights_df.columns = [
            "asset",
            "weight"
        ]

        return weights_df

    def save_outputs(self, weights_df):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "probabilistic_regime_weights.csv"
        )

        weights_df.to_csv(
            output_file,
            index=False
        )

        print("\nPROBABILISTIC REGIME ALLOCATION")
        print("=" * 60)

        print(
            weights_df.sort_values(
                "weight",
                ascending=False
            ).to_string(index=False)
        )

        print(f"\nSaved weights: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("PROBABILISTIC REGIME ALLOCATION ENGINE")
        print("=" * 60)

        regime_weights, forecast = self.load_data()

        weights_df = self.compute_probabilistic_weights(
            regime_weights,
            forecast
        )

        self.save_outputs(weights_df)


if __name__ == "__main__":

    allocator = ProbabilisticRegimeAllocator()

    allocator.run_pipeline()
