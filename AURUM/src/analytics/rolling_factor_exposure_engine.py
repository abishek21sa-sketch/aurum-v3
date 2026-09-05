import pandas as pd
from pathlib import Path


class RollingFactorExposureEngine:

    def __init__(self):

        self.backtest_path = Path("data/backtesting")
        self.risk_path = Path("data/risk")
        self.output_path = Path("data/analytics")

    def load_inputs(self):

        backtest = pd.read_csv(
            self.backtest_path / "dynamic_allocation_backtest.csv"
        )

        factor_exposures = pd.read_csv(
            self.risk_path / "factor_exposures.csv"
        )

        backtest["Date"] = pd.to_datetime(backtest["Date"])

        return backtest, factor_exposures

    def compute_rolling_exposure(self, backtest, factor_exposures):

        records = []

        for _, row in backtest.iterrows():

            total_beta = 0

            for _, factor_row in factor_exposures.iterrows():

                asset = factor_row["asset"]
                weight_col = f"{asset}_weight"

                if weight_col in backtest.columns:

                    total_beta += row[weight_col] * factor_row["beta"]

            records.append(
                {
                    "Date": row["Date"],
                    "regime": row["regime"],
                    "portfolio_beta_to_spy": total_beta
                }
            )

        exposure_df = pd.DataFrame(records)

        exposure_df["rolling_beta_20"] = (
            exposure_df["portfolio_beta_to_spy"]
            .rolling(20)
            .mean()
        )

        exposure_df["rolling_beta_60"] = (
            exposure_df["portfolio_beta_to_spy"]
            .rolling(60)
            .mean()
        )

        return exposure_df

    def save_outputs(self, exposure_df):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "rolling_factor_exposure.csv"

        exposure_df.to_csv(output_file, index=False)

        print("\nROLLING FACTOR EXPOSURE")
        print("=" * 60)
        print(exposure_df.tail().to_string(index=False))

        print(f"\nSaved rolling factor exposure: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("ROLLING FACTOR EXPOSURE ENGINE")
        print("=" * 60)

        backtest, factor_exposures = self.load_inputs()

        exposure_df = self.compute_rolling_exposure(
            backtest,
            factor_exposures
        )

        self.save_outputs(exposure_df)


if __name__ == "__main__":

    engine = RollingFactorExposureEngine()

    engine.run_pipeline()
