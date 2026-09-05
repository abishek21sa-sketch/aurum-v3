import pandas as pd
from pathlib import Path


class FactorExposureEngine:

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

        return backtest, factor_exposures

    def compute_portfolio_factor_exposure(
        self,
        backtest,
        factor_exposures
    ):

        latest_weights = backtest.tail(1)

        records = []

        for _, factor_row in factor_exposures.iterrows():

            asset = factor_row["asset"]
            weight_col = f"{asset}_weight"

            if weight_col in latest_weights.columns:

                weight = latest_weights[weight_col].iloc[0]

                records.append(
                    {
                        "asset": asset,
                        "portfolio_weight": weight,
                        "beta_to_spy": factor_row["beta"],
                        "correlation_to_spy": factor_row["correlation"],
                        "weighted_beta_contribution": weight * factor_row["beta"]
                    }
                )

        exposure_df = pd.DataFrame(records)

        total_beta = exposure_df["weighted_beta_contribution"].sum()

        exposure_df["portfolio_total_beta"] = total_beta

        return exposure_df

    def save_outputs(self, exposure_df):

        self.output_path.mkdir(parents=True, exist_ok=True)

        output_file = self.output_path / "portfolio_factor_exposure.csv"

        exposure_df.to_csv(output_file, index=False)

        print("\nPORTFOLIO FACTOR EXPOSURE")
        print("=" * 60)

        print(exposure_df.to_string(index=False))

        print(f"\nSaved factor exposure: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("PORTFOLIO FACTOR EXPOSURE ENGINE")
        print("=" * 60)

        backtest, factor_exposures = self.load_inputs()

        exposure_df = self.compute_portfolio_factor_exposure(
            backtest,
            factor_exposures
        )

        self.save_outputs(exposure_df)


if __name__ == "__main__":

    engine = FactorExposureEngine()

    engine.run_pipeline()
