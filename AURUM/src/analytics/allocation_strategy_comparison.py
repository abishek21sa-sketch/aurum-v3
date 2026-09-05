from pathlib import Path
import pandas as pd


class AllocationStrategyComparison:
    def __init__(
        self,
        output_path="data/analytics/allocation_strategy_comparison.csv",
    ):
        self.output_path = Path(output_path)

        self.strategy_files = {
            "bayesian_robust": "data/backtesting/bayesian_robust_backtest_summary.csv",
            "dynamic_allocation": "data/backtesting/dynamic_allocation_transaction_cost.csv",
            "regime_aware": "data/backtesting/regime_aware_backtest.csv",
            "rolling_min_variance": "data/backtesting/rolling_min_variance_backtest.csv",
            "institutional_portfolio": "data/institutional/portfolio_backtest_summary.csv",
            "black_litterman": "data/backtesting/black_litterman_backtest_summary.csv",
            "meta_strategy": "data/backtesting/meta_strategy_backtest_summary.csv",
            "hrp": "data/backtesting/hrp_backtest_summary.csv",
        }

    def load_strategy_summary(self, name, path):
        path = Path(path)

        if not path.exists():
            return None

        df = pd.read_csv(path)

        if len(df) == 1 and "net_total_return" in df.columns:
            row = df.iloc[0]
            return {
                "strategy": name,
                "observations": row.get("observations"),
                "net_total_return": row.get("net_total_return"),
                "volatility": row.get("net_volatility"),
                "sharpe_like": row.get("net_sharpe_like"),
                "max_drawdown": row.get("net_max_drawdown"),
                "avg_turnover": row.get("avg_turnover"),
                "transaction_cost_drag": row.get("total_transaction_cost"),
            }
        
        if len(df) == 1 and "total_return" in df.columns:
            row = df.iloc[0]
            return {
                "strategy": name,
                "observations": row.get("observations"),
                "net_total_return": row.get("total_return"),
                "volatility": row.get("volatility"),
                "sharpe_like": row.get("sharpe_like"),
                "max_drawdown": row.get("max_drawdown"),
                "avg_turnover": None,
                "transaction_cost_drag": None,
            }

        date_col = "Date" if "Date" in df.columns else None

        if "net_return" in df.columns:
            ret_col = "net_return"
        elif "portfolio_return" in df.columns:
            ret_col = "portfolio_return"
        else:
            return None

        equity = (1 + df[ret_col]).cumprod()
        running_peak = equity.cummax()
        drawdown = equity / running_peak - 1

        volatility = df[ret_col].std() * (252 ** 0.5)
        sharpe_like = (df[ret_col].mean() * 252) / (volatility + 1e-8)

        return {
            "strategy": name,
            "observations": len(df),
            "net_total_return": equity.iloc[-1] - 1,
            "volatility": volatility,
            "sharpe_like": sharpe_like,
            "max_drawdown": drawdown.min(),
            "avg_turnover": df["turnover"].mean() if "turnover" in df.columns else None,
            "transaction_cost_drag": df["transaction_cost"].sum() if "transaction_cost" in df.columns else None,
        }

    def run(self):
        rows = []

        for name, path in self.strategy_files.items():
            result = self.load_strategy_summary(name, path)
            if result is not None:
                rows.append(result)

        comparison = pd.DataFrame(rows)

        comparison = comparison.sort_values(
            ["sharpe_like", "net_total_return"],
            ascending=False,
        )

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        comparison.to_csv(self.output_path, index=False)

        print("ALLOCATION STRATEGY COMPARISON COMPLETE")
        print("=" * 70)
        print(comparison.to_string(index=False))
        print()
        print(f"Saved comparison: {self.output_path}")

        return comparison


if __name__ == "__main__":
    engine = AllocationStrategyComparison()
    engine.run()