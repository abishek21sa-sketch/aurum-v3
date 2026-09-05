from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class CrossSectionalAlphaEngine:
    def __init__(self):
        self.processed_dir = Path("data/processed")
        self.regime_path = Path("data/regimes/calibrated_regime_probabilities.csv")

        self.output_dir = Path("data/signals")
        self.signal_output_path = self.output_dir / "cross_sectional_alpha_signals.csv"
        self.summary_output_path = self.output_dir / "cross_sectional_alpha_summary.csv"

    def load_inputs(self):
        logger.info("Loading processed datasets from: %s", self.processed_dir)
        logger.info("Loading calibrated regimes from: %s", self.regime_path)

        self.regimes = pd.read_csv(self.regime_path)
        self.regimes["Date"] = pd.to_datetime(self.regimes["Date"])

        self.datasets = {}

        for file in sorted(self.processed_dir.glob("*_processed.csv")):
            ticker = file.stem.replace("_processed", "")
            df = pd.read_csv(file)
            df["Date"] = pd.to_datetime(df["Date"])
            self.datasets[ticker] = df

        logger.info("Loaded tickers: %s", list(self.datasets.keys()))
        logger.info("Loaded regimes shape: %s", self.regimes.shape)

    def build_price_matrix(self):
        logger.info("Building price matrix.")

        frames = []

        for ticker, df in self.datasets.items():
            temp = df[["Date", "Close"]].copy()
            temp = temp.rename(columns={"Close": ticker})
            frames.append(temp.set_index("Date"))

        self.price_matrix = (
            pd.concat(frames, axis=1, sort=True)
            .sort_index()
            .ffill()
        )

        logger.info("Price matrix shape: %s", self.price_matrix.shape)
        logger.info("Price columns: %s", list(self.price_matrix.columns))

    def build_factor_features(self):
        logger.info("Building factor research features.")

        prices = self.price_matrix.copy()

        returns_5d = prices.pct_change(5, fill_method=None)
        returns_20d = prices.pct_change(20, fill_method=None)
        returns_60d = prices.pct_change(60, fill_method=None)

        daily_returns = prices.pct_change(fill_method=None)

        realized_vol = daily_returns.rolling(20).std() * np.sqrt(252)

        trend_strength = (prices.rolling(20).mean() / prices.rolling(60).mean()) - 1

        rows = []

        for date in prices.index:
            cross_section = pd.DataFrame(
                {
                    "asset": prices.columns,
                    "momentum_5d": returns_5d.loc[date].values,
                    "momentum_20d": returns_20d.loc[date].values,
                    "momentum_60d": returns_60d.loc[date].values,
                    "realized_vol": realized_vol.loc[date].values,
                    "trend_strength": trend_strength.loc[date].values,
                }
            ).dropna()

            if len(cross_section) < 4:
                continue

            cross_section["vol_adjusted_momentum"] = (
                cross_section["momentum_20d"] / cross_section["realized_vol"]
            )

            factor_cols = [
                "momentum_5d",
                "momentum_20d",
                "momentum_60d",
                "vol_adjusted_momentum",
                "trend_strength",
            ]

            for col in factor_cols:
                std = cross_section[col].std()

                if std == 0 or np.isnan(std):
                    cross_section[f"{col}_zscore"] = 0.0
                else:
                    cross_section[f"{col}_zscore"] = (
                        cross_section[col] - cross_section[col].mean()
                    ) / std

            cross_section["composite_alpha_score"] = (
                0.20 * cross_section["momentum_5d_zscore"]
                + 0.30 * cross_section["momentum_20d_zscore"]
                + 0.20 * cross_section["momentum_60d_zscore"]
                + 0.20 * cross_section["vol_adjusted_momentum_zscore"]
                + 0.10 * cross_section["trend_strength_zscore"]
            )

            cross_section["alpha_rank"] = (
                cross_section["composite_alpha_score"].rank(pct=True)
            )

            cross_section["Date"] = date
            rows.append(cross_section)

        if not rows:
            raise ValueError("No alpha rows generated. Check price matrix and date overlap.")

        self.alpha_signals = pd.concat(rows, ignore_index=True)

        logger.info("Raw alpha signal preview:\n%s", self.alpha_signals.tail())

    def apply_regime_conditioning(self):
        logger.info("Applying regime-aware alpha weighting.")

        regime_cols = [
            "Date",
            "calibrated_state_0_probability",
            "calibrated_state_1_probability",
            "calibrated_state_2_probability",
            "calibrated_most_likely_state",
        ]

        df = self.alpha_signals.merge(
            self.regimes[regime_cols],
            on="Date",
            how="inner",
        )

        regime_multiplier = (
            0.55 * df["calibrated_state_0_probability"]
            + 1.20 * df["calibrated_state_1_probability"]
            + 0.90 * df["calibrated_state_2_probability"]
        )

        df["regime_adjusted_alpha"] = (
            df["composite_alpha_score"] * regime_multiplier
        )

        df["allocation_preference_rank"] = (
            df.groupby("Date")["regime_adjusted_alpha"].rank(pct=True)
        )

        dispersion = (
            df.groupby("Date")["regime_adjusted_alpha"]
            .std()
            .rename("alpha_dispersion")
            .reset_index()
        )

        self.alpha_signals = df.merge(dispersion, on="Date", how="left")

        logger.info("Regime-adjusted alpha preview:\n%s", self.alpha_signals.tail())

    def build_summary(self):
        logger.info("Building alpha research summary.")

        self.summary = (
            self.alpha_signals.groupby("asset")
            .agg(
                observations=("asset", "count"),
                avg_composite_alpha=("composite_alpha_score", "mean"),
                avg_regime_adjusted_alpha=("regime_adjusted_alpha", "mean"),
                avg_alpha_rank=("allocation_preference_rank", "mean"),
                avg_realized_vol=("realized_vol", "mean"),
                avg_alpha_dispersion=("alpha_dispersion", "mean"),
            )
            .reset_index()
            .sort_values("avg_regime_adjusted_alpha", ascending=False)
        )

        logger.info("Alpha summary:\n%s", self.summary.round(4))

    def save_outputs(self):
        logger.info("Saving alpha outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.alpha_signals.to_csv(self.signal_output_path, index=False)
        self.summary.to_csv(self.summary_output_path, index=False)

        logger.info("Saved alpha signals to: %s", self.signal_output_path)
        logger.info("Saved alpha summary to: %s", self.summary_output_path)

    def run(self):
        logger.info("Starting Cross-Sectional Alpha Engine v2.")

        self.load_inputs()
        self.build_price_matrix()
        self.build_factor_features()
        self.apply_regime_conditioning()
        self.build_summary()
        self.save_outputs()

        logger.info("Cross-Sectional Alpha Engine v2 completed successfully.")


if __name__ == "__main__":
    engine = CrossSectionalAlphaEngine()
    engine.run()