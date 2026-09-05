from pathlib import Path
import numpy as np
import pandas as pd


class MetaStrategyAllocator:
    def __init__(
        self,
        comparison_path="data/analytics/allocation_strategy_comparison.csv",
        output_path="data/optimization/meta_strategy_weights.csv",
        max_strategy_weight=0.40,
    ):
        self.comparison_path = Path(comparison_path)
        self.output_path = Path(output_path)
        self.max_strategy_weight = max_strategy_weight

    def run(self):
        df = pd.read_csv(self.comparison_path)
        df = df[df["strategy"] != "meta_strategy"].copy()

        df = df.dropna(subset=["sharpe_like", "net_total_return", "max_drawdown"])

        df["drawdown_penalty"] = df["max_drawdown"].abs()
        df["turnover_penalty"] = df["avg_turnover"].fillna(0.0)

        df["meta_score"] = (
            df["sharpe_like"]
            + 0.75 * df["net_total_return"]
            - 1.50 * df["drawdown_penalty"]
            - 0.50 * df["turnover_penalty"]
        )

        df["meta_score"] = df["meta_score"].clip(lower=0)

        if df["meta_score"].sum() <= 0:
            df["raw_meta_weight"] = 1.0 / len(df)
        else:
            df["raw_meta_weight"] = df["meta_score"] / df["meta_score"].sum()

        df["meta_weight"] = df["raw_meta_weight"].clip(upper=self.max_strategy_weight)
        df["meta_weight"] = df["meta_weight"] / df["meta_weight"].sum()

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.output_path, index=False)

        print("META STRATEGY ALLOCATOR COMPLETE")
        print("=" * 70)
        print(df[[
            "strategy",
            "net_total_return",
            "sharpe_like",
            "max_drawdown",
            "avg_turnover",
            "meta_score",
            "meta_weight",
        ]].to_string(index=False))
        print()
        print(f"Saved meta strategy weights: {self.output_path}")

        return df


if __name__ == "__main__":
    allocator = MetaStrategyAllocator()
    allocator.run()