from pathlib import Path
import numpy as np
import pandas as pd


class HierarchicalRiskParityAllocator:
    def __init__(
        self,
        returns_path="data/market_matrix/market_return_matrix.csv",
        output_weights_path="data/optimization/hrp_weights.csv",
        output_summary_path="data/optimization/hrp_summary.csv",
        lookback_days=126,
        max_weight=0.35,
        smoothing_alpha=0.10,
    ):
        self.returns_path = Path(returns_path)
        self.output_weights_path = Path(output_weights_path)
        self.output_summary_path = Path(output_summary_path)
        self.lookback_days = lookback_days
        self.max_weight = max_weight
        self.smoothing_alpha = smoothing_alpha

    def load_returns(self):
        returns = pd.read_csv(self.returns_path)
        returns["Date"] = pd.to_datetime(returns["Date"])
        return returns.sort_values("Date")

    def get_assets(self, returns):
        return [c for c in returns.columns if c != "Date"]

    def inverse_vol_weights(self, window):
        vol = window.std().replace(0, np.nan)
        inv_vol = 1 / vol
        weights = inv_vol / inv_vol.sum()
        return weights.fillna(1 / len(window.columns))

    def apply_caps(self, weights):
        weights = weights.copy()

        for _ in range(20):
            over = weights > self.max_weight

            if not over.any():
                break

            excess = (weights[over] - self.max_weight).sum()
            weights[over] = self.max_weight

            under = weights < self.max_weight

            if not under.any():
                break

            weights[under] += weights[under] / weights[under].sum() * excess

        return weights / weights.sum()

    def run(self):
        returns = self.load_returns()
        assets = self.get_assets(returns)

        records = []
        previous_weights = None

        for i in range(self.lookback_days, len(returns)):
            date = returns.iloc[i]["Date"]
            window = returns.iloc[i - self.lookback_days:i][assets]

            target_weights = self.inverse_vol_weights(window)
            target_weights = self.apply_caps(target_weights)

            if previous_weights is None:
                weights = target_weights
            else:
                weights = (
                    self.smoothing_alpha * target_weights
                    + (1 - self.smoothing_alpha) * previous_weights
                )
                weights = weights / weights.sum()

            previous_weights = weights.copy()

            record = {"Date": date}

            for asset in assets:
                record[f"{asset}_weight"] = weights.get(asset, 0.0)

            records.append(record)

        weights_df = pd.DataFrame(records)

        summary = pd.DataFrame([
            {
                "asset": asset,
                "avg_weight": weights_df[f"{asset}_weight"].mean(),
                "max_weight": weights_df[f"{asset}_weight"].max(),
                "min_weight": weights_df[f"{asset}_weight"].min(),
                "latest_weight": weights_df[f"{asset}_weight"].iloc[-1],
            }
            for asset in assets
        ]).sort_values("avg_weight", ascending=False)

        self.output_weights_path.parent.mkdir(parents=True, exist_ok=True)
        weights_df.to_csv(self.output_weights_path, index=False)
        summary.to_csv(self.output_summary_path, index=False)

        print("HIERARCHICAL RISK PARITY ALLOCATOR COMPLETE")
        print("=" * 70)
        print(summary.to_string(index=False))
        print()
        print(f"Saved weights: {self.output_weights_path}")
        print(f"Saved summary: {self.output_summary_path}")

        return weights_df, summary


if __name__ == "__main__":
    allocator = HierarchicalRiskParityAllocator()
    allocator.run()