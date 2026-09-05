from pathlib import Path
import numpy as np
import pandas as pd


class BayesianRobustBacktest:
    def __init__(
        self,
        weights_path="data/optimization/bayesian_robust_weights.csv",
        returns_path="data/market_matrix/market_return_matrix.csv",
        output_path="data/backtesting/bayesian_robust_backtest.csv",
        summary_path="data/backtesting/bayesian_robust_backtest_summary.csv",
        transaction_cost_bps=10,
    ):
        self.weights_path = Path(weights_path)
        self.returns_path = Path(returns_path)
        self.output_path = Path(output_path)
        self.summary_path = Path(summary_path)
        self.transaction_cost_bps = transaction_cost_bps

    def load_data(self):
        weights = pd.read_csv(self.weights_path)
        returns = pd.read_csv(self.returns_path)

        weights["Date"] = pd.to_datetime(weights["Date"])
        returns["Date"] = pd.to_datetime(returns["Date"])

        return weights, returns

    def get_assets(self, weights):
        return sorted(
            list(
                set(
                    c.replace("_weight", "")
                    for c in weights.columns
                    if c.endswith("_weight")
                )
            )
        )

    def compute_turnover(self, current_weights, previous_weights):
        return np.abs(current_weights - previous_weights).sum()

    def run(self):
        weights, returns = self.load_data()

        assets = self.get_assets(weights)

        merged = weights.merge(returns, on="Date", how="inner")

        portfolio_returns = []
        previous_weights = None

        for _, row in merged.iterrows():

            weight_vector = np.array(
                [row.get(f"{a}_weight", 0.0) for a in assets]
            )

            return_vector = np.array(
                [row.get(a, 0.0) for a in assets]
            )

            gross_return = np.dot(weight_vector, return_vector)

            if previous_weights is None:
                turnover = 0.0
            else:
                turnover = self.compute_turnover(
                    weight_vector,
                    previous_weights,
                )

            transaction_cost = turnover * (self.transaction_cost_bps / 10000)

            net_return = gross_return - transaction_cost

            portfolio_returns.append({
                "Date": row["Date"],
                "gross_return": gross_return,
                "turnover": turnover,
                "transaction_cost": transaction_cost,
                "net_return": net_return,
            })

            previous_weights = weight_vector

        backtest = pd.DataFrame(portfolio_returns)

        backtest["gross_equity_curve"] = (
            1 + backtest["gross_return"]
        ).cumprod()

        backtest["net_equity_curve"] = (
            1 + backtest["net_return"]
        ).cumprod()

        backtest["gross_running_peak"] = (
            backtest["gross_equity_curve"]
        ).cummax()

        backtest["net_running_peak"] = (
            backtest["net_equity_curve"]
        ).cummax()

        backtest["gross_drawdown"] = (
            backtest["gross_equity_curve"]
            / backtest["gross_running_peak"]
            - 1
        )

        backtest["net_drawdown"] = (
            backtest["net_equity_curve"]
            / backtest["net_running_peak"]
            - 1
        )

        gross_vol = backtest["gross_return"].std() * np.sqrt(252)
        net_vol = backtest["net_return"].std() * np.sqrt(252)

        gross_sharpe = (
            backtest["gross_return"].mean() * 252
        ) / (gross_vol + 1e-8)

        net_sharpe = (
            backtest["net_return"].mean() * 252
        ) / (net_vol + 1e-8)

        summary = pd.DataFrame([{
            "observations": len(backtest),
            "gross_total_return":
                backtest["gross_equity_curve"].iloc[-1] - 1,
            "net_total_return":
                backtest["net_equity_curve"].iloc[-1] - 1,
            "gross_volatility": gross_vol,
            "net_volatility": net_vol,
            "gross_sharpe_like": gross_sharpe,
            "net_sharpe_like": net_sharpe,
            "gross_max_drawdown":
                backtest["gross_drawdown"].min(),
            "net_max_drawdown":
                backtest["net_drawdown"].min(),
            "avg_turnover":
                backtest["turnover"].mean(),
            "total_transaction_cost":
                backtest["transaction_cost"].sum(),
        }])

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        backtest.to_csv(self.output_path, index=False)
        summary.to_csv(self.summary_path, index=False)

        print("BAYESIAN ROBUST BACKTEST COMPLETE")
        print("=" * 60)
        print(summary.to_string(index=False))

        return backtest, summary


if __name__ == "__main__":
    engine = BayesianRobustBacktest()
    engine.run()