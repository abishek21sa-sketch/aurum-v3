import pandas as pd
from pathlib import Path


class RegimeForecastEngine:

    def __init__(self):

        self.regime_path = Path("data/regimes")
        self.output_path = Path("data/regimes")

    def load_data(self):

        regimes = pd.read_csv(
            self.regime_path / "market_regimes.csv"
        )

        transition_matrix = pd.read_csv(
            self.regime_path / "regime_transition_matrix.csv",
            index_col=0
        )

        regimes["Date"] = pd.to_datetime(regimes["Date"])

        return regimes.sort_values("Date"), transition_matrix

    def forecast_next_regime_probabilities(
        self,
        regimes,
        transition_matrix
    ):

        latest_regime = regimes["regime"].iloc[-1]

        next_probs = transition_matrix.loc[
            latest_regime
        ].reset_index()

        next_probs.columns = [
            "next_regime",
            "probability"
        ]

        next_probs["current_regime"] = latest_regime

        next_probs = next_probs[
            [
                "current_regime",
                "next_regime",
                "probability"
            ]
        ]

        return latest_regime, next_probs

    def save_outputs(self, latest_regime, next_probs):

        output_file = (
            self.output_path /
            "next_regime_forecast.csv"
        )

        next_probs.to_csv(
            output_file,
            index=False
        )

        print("\nREGIME FORECAST")
        print("=" * 60)

        print(f"Current Regime: {latest_regime}")

        print("\nNext-Regime Probabilities:")
        print(
            next_probs.sort_values(
                "probability",
                ascending=False
            ).to_string(index=False)
        )

        print(f"\nSaved forecast: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("REGIME FORECAST ENGINE")
        print("=" * 60)

        regimes, transition_matrix = self.load_data()

        latest_regime, next_probs = (
            self.forecast_next_regime_probabilities(
                regimes,
                transition_matrix
            )
        )

        self.save_outputs(
            latest_regime,
            next_probs
        )


if __name__ == "__main__":

    engine = RegimeForecastEngine()

    engine.run_pipeline()
