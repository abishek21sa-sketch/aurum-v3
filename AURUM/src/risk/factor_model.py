import pandas as pd
import numpy as np
from pathlib import Path


class FactorModel:

    def __init__(self):

        self.matrix_path = Path("data/market_matrix")
        self.output_path = Path("data/risk")

    def load_returns(self):

        df = pd.read_csv(
            self.matrix_path / "market_return_matrix.csv"
        )

        df["Date"] = pd.to_datetime(df["Date"])

        return df.sort_values("Date")

    def compute_beta(self, asset_returns, factor_returns):

        covariance = np.cov(
            asset_returns,
            factor_returns
        )[0, 1]

        factor_variance = np.var(factor_returns)

        beta = (
            covariance / factor_variance
            if factor_variance > 0
            else 0
        )

        return beta

    def compute_factor_exposures(self, df, factor_col="SPY"):

        asset_cols = [
            col for col in df.columns
            if col != "Date"
        ]

        factor_returns = df[factor_col]

        records = []

        for asset in asset_cols:

            if asset == factor_col:
                beta = 1.0
                correlation = 1.0
            else:
                beta = self.compute_beta(
                    df[asset],
                    factor_returns
                )

                correlation = df[asset].corr(
                    factor_returns
                )

            records.append(
                {
                    "asset": asset,
                    "factor": factor_col,
                    "beta": beta,
                    "correlation": correlation,
                    "mean_return": df[asset].mean(),
                    "volatility": df[asset].std()
                }
            )

        exposures = pd.DataFrame(records)

        return exposures

    def save_outputs(self, exposures):

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            self.output_path /
            "factor_exposures.csv"
        )

        exposures.to_csv(
            output_file,
            index=False
        )

        print("\nFACTOR EXPOSURE MODEL")
        print("=" * 60)

        print(
            exposures.sort_values(
                "beta",
                ascending=False
            ).to_string(index=False)
        )

        print(f"\nSaved factor exposures: {output_file}")

    def run_pipeline(self):

        print("=" * 60)
        print("FACTOR MODEL ENGINE")
        print("=" * 60)

        df = self.load_returns()

        exposures = self.compute_factor_exposures(
            df,
            factor_col="SPY"
        )

        self.save_outputs(exposures)


if __name__ == "__main__":

    model = FactorModel()

    model.run_pipeline()
    
