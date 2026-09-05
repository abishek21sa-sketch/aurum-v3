import pandas as pd
from pathlib import Path


class ConfidenceAdjustedAllocator:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.regime_path = Path("data/regimes")
        self.output_path = Path("data/optimization")

    def load_inputs(self):

        weights = pd.read_csv(
            self.optimization_path / "probabilistic_regime_weights.csv"
        )

        stability = pd.read_csv(
            self.regime_path / "regime_stability.csv"
        )

        return weights, stability

    def compute_adjusted_allocation(self, weights, stability):

        latest_instability = stability["instability_score"].iloc[-1]

        risk_assets = [
            "SPY",
            "QQQ",
            "DIA",
            "BTC-USD",
            "ETH-USD"
        ]

        defensive_assets = [
            "TLT",
            "GLD",
            "VIX"
        ]

        risk_scale = max(
            0.50,
            1 - latest_instability
        )

        adjusted = weights.copy()

        adjusted.loc[
            adjusted["asset"].isin(risk_assets),
            "weight"
        ] *= risk_scale

        released_weight = (
            1 - adjusted["weight"].sum()
        )

        defensive_mask = adjusted["asset"].isin(defensive_assets)

        defensive_total = adjusted.loc[
            defensive_mask,
            "weight"
        ].sum()

        if defensive_total > 0:

            adjusted.loc[
                defensive_mask,
                "weight"
            ] += (
                adjusted.loc[
                    defensive_mask,
                    "weight"
                ]
                / defensive_total
                * released_weight
            )

        adjusted["weight"] = (
            adjusted["weight"] /
            adjusted["weight"].sum()
        )

        adjusted["instability_score"] = latest_instability
        adjusted["risk_scale"] = risk_scale

        return adjusted

    def save_outputs(self, adjusted):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = (
            self.output_path /
            "confidence_adjusted_weights.csv"
        )

        adjusted.to_csv(output_file, index=False)

        print("\nCONFIDENCE-ADJUSTED ALLOCATION")
        print("=" * 60)

        print(
            adjusted.sort_values(
                "weight",
                ascending=False
            ).to_string(index=False)
        )

        print(f"\nSaved adjusted weights: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("CONFIDENCE-ADJUSTED ALLOCATION ENGINE")
        print("=" * 60)

        weights, stability = self.load_inputs()

        adjusted = self.compute_adjusted_allocation(
            weights,
            stability
        )

        self.save_outputs(adjusted)


if __name__ == "__main__":

    allocator = ConfidenceAdjustedAllocator()

    allocator.run_pipeline()
