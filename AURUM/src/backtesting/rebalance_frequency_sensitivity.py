import pandas as pd
from pathlib import Path


class RebalanceFrequencySensitivity:

    def __init__(self):

        self.input_path = Path("data/backtesting")
        self.output_path = Path("data/backtesting")

    def load_dynamic_backtest(self):

        df = pd.read_csv(
            self.input_path / "dynamic_allocation_transaction_cost.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df

    def run_sensitivity(self, df):

        frequencies = [5, 10, 20, 40, 60]
        records = []

        for frequency in frequencies:

            sampled = df.iloc[::frequency].copy()

            total_return = sampled["net_cumulative_return"].iloc[-1]
            max_drawdown = sampled["net_drawdown"].min()
            avg_transaction_cost = sampled["transaction_cost"].mean()
            total_transaction_cost = sampled["transaction_cost"].sum()

            records.append(
                {
                    "rebalance_frequency_days": frequency,
                    "sampled_observations": len(sampled),
                    "net_total_return": total_return,
                    "max_net_drawdown": max_drawdown,
                    "average_transaction_cost": avg_transaction_cost,
                    "total_transaction_cost": total_transaction_cost
                }
            )

        return pd.DataFrame(records)

    def save_outputs(self, sensitivity_df):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "rebalance_frequency_sensitivity.csv"

        sensitivity_df.to_csv(output_file, index=False)

        print("\nREBALANCE FREQUENCY SENSITIVITY")
        print("=" * 60)
        print(sensitivity_df.to_string(index=False))

        print(f"\nSaved sensitivity results: {output_file}")

    def run(self):

        print("=" * 60)
        print("REBALANCE FREQUENCY SENSITIVITY ENGINE")
        print("=" * 60)

        df = self.load_dynamic_backtest()

        sensitivity_df = self.run_sensitivity(df)

        self.save_outputs(sensitivity_df)


if __name__ == "__main__":

    engine = RebalanceFrequencySensitivity()

    engine.run()
