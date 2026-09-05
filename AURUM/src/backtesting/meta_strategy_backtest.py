from pathlib import Path
import pandas as pd
import numpy as np


class MetaStrategyBacktest:
    def __init__(
        self,
        meta_weights_path="data/optimization/meta_strategy_weights.csv",
        output_path="data/backtesting/meta_strategy_backtest.csv",
        summary_path="data/backtesting/meta_strategy_backtest_summary.csv",
    ):
        self.meta_weights_path = Path(meta_weights_path)
        self.output_path = Path(output_path)
        self.summary_path = Path(summary_path)

        self.strategy_return_files = {
            "rolling_min_variance":
                "data/backtesting/rolling_min_variance_backtest.csv",

            "dynamic_allocation":
                "data/backtesting/dynamic_allocation_transaction_cost.csv",

            "regime_aware":
                "data/backtesting/regime_aware_backtest.csv",

            "black_litterman":
                "data/backtesting/black_litterman_backtest.csv",

            "bayesian_robust":
                "data/backtesting/bayesian_robust_backtest.csv",
        }

    def load_meta_weights(self):
        return pd.read_csv(self.meta_weights_path)

    def load_strategy_returns(self):
        strategy_frames = []

        for strategy, path in self.strategy_return_files.items():

            path = Path(path)

            if not path.exists():
                continue

            df = pd.read_csv(path)

            if "Date" not in df.columns:
                continue

            df["Date"] = pd.to_datetime(df["Date"])

            if "net_return" in df.columns:
                ret_col = "net_return"

            elif "portfolio_return" in df.columns:
                ret_col = "portfolio_return"

            else:
                continue

            strategy_df = df[["Date", ret_col]].copy()
            strategy_df.columns = ["Date", strategy]

            strategy_frames.append(strategy_df)

        merged = strategy_frames[0]

        for df in strategy_frames[1:]:
            merged = merged.merge(df, on="Date", how="inner")

        return merged.sort_values("Date")

    def run(self):
        meta_weights = self.load_meta_weights()
        strategy_returns = self.load_strategy_returns()

        weight_map = dict(
            zip(
                meta_weights["strategy"],
                meta_weights["meta_weight"],
            )
        )

        strategy_cols = [
            c for c in strategy_returns.columns
            if c != "Date"
        ]

        weights = np.array([
            weight_map.get(c, 0.0)
            for c in strategy_cols
        ])

        returns_matrix = strategy_returns[strategy_cols].values

        strategy_returns["meta_return"] = returns_matrix.dot(weights)

        strategy_returns["equity_curve"] = (
            1 + strategy_returns["meta_return"]
        ).cumprod()

        strategy_returns["running_peak"] = (
            strategy_returns["equity_curve"]
        ).cummax()

        strategy_returns["drawdown"] = (
            strategy_returns["equity_curve"]
            / strategy_returns["running_peak"]
            - 1
        )

        volatility = (
            strategy_returns["meta_return"].std()
            * np.sqrt(252)
        )

        sharpe_like = (
            strategy_returns["meta_return"].mean() * 252
        ) / (volatility + 1e-8)

        summary = pd.DataFrame([{
            "observations": len(strategy_returns),
            "total_return":
                strategy_returns["equity_curve"].iloc[-1] - 1,
            "volatility": volatility,
            "sharpe_like": sharpe_like,
            "max_drawdown":
                strategy_returns["drawdown"].min(),
        }])

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        strategy_returns.to_csv(self.output_path, index=False)
        summary.to_csv(self.summary_path, index=False)

        print("META STRATEGY BACKTEST COMPLETE")
        print("=" * 70)
        print(summary.to_string(index=False))
        print()
        print("Strategy weights:")
        print(meta_weights[[
            "strategy",
            "meta_weight"
        ]].to_string(index=False))
        print()
        print(f"Saved backtest: {self.output_path}")
        print(f"Saved summary: {self.summary_path}")

        return strategy_returns, summary


if __name__ == "__main__":
    engine = MetaStrategyBacktest()
    engine.run()