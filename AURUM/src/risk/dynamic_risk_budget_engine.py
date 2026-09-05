import pandas as pd
from pathlib import Path


class DynamicRiskBudgetEngine:

    def __init__(self):

        self.optimization_path = Path("data/optimization")
        self.regime_path = Path("data/regimes")
        self.output_path = Path("data/risk")

    def load_inputs(self):

        weights = pd.read_csv(
            self.optimization_path / "confidence_adjusted_weights.csv"
        )

        stability = pd.read_csv(
            self.regime_path / "regime_stability.csv"
        )

        return weights, stability

    def compute_target_exposure(self, instability_score):

        target_exposure = max(
            0.40,
            1 - instability_score
        )

        return target_exposure

    def compute_risk_budget(self, weights, stability):

        latest_instability = stability["instability_score"].iloc[-1]

        target_exposure = self.compute_target_exposure(
            latest_instability
        )

        allocation = weights[["asset", "weight"]].copy()

        allocation["scaled_weight"] = (
            allocation["weight"] * target_exposure
        )

        reserve_weight = 1 - allocation["scaled_weight"].sum()

        reserve_row = pd.DataFrame([
            {
                "asset": "CASH_RESERVE",
                "weight": 0.0,
                "scaled_weight": reserve_weight
            }
        ])

        allocation = pd.concat(
            [allocation, reserve_row],
            ignore_index=True
        )

        allocation["instability_score"] = latest_instability
        allocation["target_exposure"] = target_exposure

        return allocation

    def save_outputs(self, allocation):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "dynamic_risk_budget.csv"

        allocation.to_csv(output_file, index=False)

        print("\nDYNAMIC RISK BUDGET")
        print("=" * 60)

        print(
            allocation.sort_values(
                "scaled_weight",
                ascending=False
            ).to_string(index=False)
        )

        print(f"\nSaved risk budget: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("DYNAMIC RISK BUDGET ENGINE")
        print("=" * 60)

        weights, stability = self.load_inputs()

        allocation = self.compute_risk_budget(
            weights,
            stability
        )

        self.save_outputs(allocation)


if __name__ == "__main__":

    engine = DynamicRiskBudgetEngine()

    engine.run_pipeline()
