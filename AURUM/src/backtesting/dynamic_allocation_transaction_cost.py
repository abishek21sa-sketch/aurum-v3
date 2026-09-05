import pandas as pd
import numpy as np
from pathlib import Path


class DynamicAllocationTransactionCostBacktester:

    def __init__(self):

        self.input_path = Path("data/backtesting")
        self.output_path = Path("data/backtesting")

    def load_dynamic_backtest(self):

        df = pd.read_csv(
            self.input_path / "dynamic_allocation_backtest.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def apply_transaction_costs(
        self,
        df,
        transaction_cost_rate=0.001
    ):

        df = df.copy()

        df["turnover"] = (
            df["portfolio_return"]
            .diff()
            .abs()
            .fillna(0)
        )

        df["transaction_cost"] = (
            df["turnover"] * transaction_cost_rate
        )

        df["net_return"] = (
            df["portfolio_return"] - df["transaction_cost"]
        )

        df["net_cumulative_return"] = (
            1 + df["net_return"]
        ).cumprod() - 1

        df["net_running_max"] = (
            1 + df["net_cumulative_return"]
        ).cummax()

        df["net_drawdown"] = (
            (1 + df["net_cumulative_return"])
            / df["net_running_max"]
            - 1
        )

        return df

    def save_outputs(self, df):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = (
            self.output_path /
            "dynamic_allocation_transaction_cost.csv"
        )

        df.to_csv(output_file, index=False)

        total_return = df["net_cumulative_return"].iloc[-1]

        annualized_return = (
            (1 + total_return) ** (252 / len(df)) - 1
        )

        annualized_volatility = (
            df["net_return"].std() * np.sqrt(252)
        )

        sharpe_ratio = (
            annualized_return / annualized_volatility
            if annualized_volatility > 0
            else 0
        )

        max_drawdown = df["net_drawdown"].min()
        total_transaction_cost = df["transaction_cost"].sum()
        average_turnover = df["turnover"].mean()

        print("\nDYNAMIC ALLOCATION WITH TRANSACTION COSTS")
        print("=" * 60)

        print(f"Net Total Return: {total_return:.6f}")
        print(f"Annualized Net Return: {annualized_return:.6f}")
        print(f"Annualized Net Volatility: {annualized_volatility:.6f}")
        print(f"Net Sharpe Ratio: {sharpe_ratio:.6f}")
        print(f"Max Net Drawdown: {max_drawdown:.6f}")
        print(f"Total Transaction Cost: {total_transaction_cost:.6f}")
        print(f"Average Turnover Proxy: {average_turnover:.6f}")

        print(f"\nSaved backtest: {output_file}")

    def run(self):

        print("=" * 60)
        print("DYNAMIC ALLOCATION TRANSACTION COST ENGINE")
        print("=" * 60)

        df = self.load_dynamic_backtest()

        net_df = self.apply_transaction_costs(
            df,
            transaction_cost_rate=0.001
        )

        self.save_outputs(net_df)


if __name__ == "__main__":

    backtester = DynamicAllocationTransactionCostBacktester()

    backtester.run()
