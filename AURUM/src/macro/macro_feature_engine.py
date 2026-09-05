from pathlib import Path
import logging

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class MacroFeatureEngine:
    """
    Macro Feature Engine v2 for AURUM.

    Builds institutional macro features:
    - volatility features
    - VIX stress features
    - momentum features
    - cross-asset stress
    - yield-spread proxy
    - VIX term-structure proxy
    - inflation proxy
    - liquidity proxy
    - volatility regime score
    - momentum breadth
    """

    def __init__(self):
        self.input_dir = Path("data/processed")
        self.output_dir = Path("data/features")
        self.output_path = self.output_dir / "macro_features.parquet"
        self.preview_path = self.output_dir / "macro_features_preview.csv"
        self.summary_path = self.output_dir / "macro_features_summary.csv"

    def load_data(self):
        logger.info("Loading market datasets.")

        self.datasets = {}

        for csv_file in self.input_dir.glob("*_processed.csv"):
            ticker = csv_file.stem.replace("_processed", "")
            logger.info("Loading %s", ticker)

            df = pd.read_csv(csv_file)
            df["Date"] = pd.to_datetime(df["Date"])

            logger.info("%s columns: %s", ticker, list(df.columns))
            logger.info("%s shape: %s", ticker, df.shape)

            self.datasets[ticker] = df

        logger.info("Loaded datasets: %s", list(self.datasets.keys()))

    def build_price_matrix(self):
        logger.info("Building close price matrix.")

        price_frames = []

        for ticker, df in self.datasets.items():
            temp = df[["Date", "Close"]].copy()
            temp = temp.rename(columns={"Close": ticker})
            temp = temp.set_index("Date")

            price_frames.append(temp)

        self.price_matrix = pd.concat(price_frames, axis=1, sort=True).sort_index()
        self.price_matrix = self.price_matrix.ffill()

        logger.info("Price matrix shape: %s", self.price_matrix.shape)
        logger.info("Price matrix columns: %s", list(self.price_matrix.columns))

    def build_return_matrix(self):
        logger.info("Building return matrix.")

        self.return_matrix = self.price_matrix.pct_change(fill_method=None)

        logger.info("Return matrix shape: %s", self.return_matrix.shape)
        logger.info("Return matrix preview:\n%s", self.return_matrix.tail().round(4))

    def initialize_features(self):
        logger.info("Initializing macro feature dataframe.")

        self.features = pd.DataFrame(index=self.price_matrix.index)

    def build_volatility_features(self):
        logger.info("Building volatility and VIX features.")

        self.features["spy_vol_20d"] = (
            self.return_matrix["SPY"].rolling(window=20).std() * (252 ** 0.5)
        )

        self.features["qqq_vol_20d"] = (
            self.return_matrix["QQQ"].rolling(window=20).std() * (252 ** 0.5)
        )

        self.features["btc_vol_20d"] = (
            self.return_matrix["BTC-USD"].rolling(window=20).std() * (252 ** 0.5)
        )

        self.features["vix_level"] = self.price_matrix["VIX"]
        self.features["vix_ma_20d"] = self.price_matrix["VIX"].rolling(window=20).mean()

        self.features["vix_stress_ratio"] = (
            self.features["vix_level"] / self.features["vix_ma_20d"]
        )

        logger.info(
            "Volatility feature preview:\n%s",
            self.features[
                [
                    "spy_vol_20d",
                    "qqq_vol_20d",
                    "btc_vol_20d",
                    "vix_level",
                    "vix_ma_20d",
                    "vix_stress_ratio",
                ]
            ].tail().round(4),
        )

    def build_momentum_features(self):
        logger.info("Building momentum features.")

        self.features["spy_momentum_20d"] = self.price_matrix["SPY"].pct_change(periods=20)
        self.features["qqq_momentum_20d"] = self.price_matrix["QQQ"].pct_change(periods=20)
        self.features["tlt_momentum_20d"] = self.price_matrix["TLT"].pct_change(periods=20)
        self.features["gld_momentum_20d"] = self.price_matrix["GLD"].pct_change(periods=20)
        self.features["btc_momentum_20d"] = self.price_matrix["BTC-USD"].pct_change(periods=20)

        momentum_cols = [
            "spy_momentum_20d",
            "qqq_momentum_20d",
            "tlt_momentum_20d",
            "gld_momentum_20d",
            "btc_momentum_20d",
        ]

        self.features["momentum_breadth"] = (
            self.features[momentum_cols].gt(0).sum(axis=1) / len(momentum_cols)
        )

        logger.info(
            "Momentum feature preview:\n%s",
            self.features[momentum_cols + ["momentum_breadth"]].tail().round(4),
        )

    def build_cross_asset_features(self):
        logger.info("Building cross-asset stress features.")

        self.features["spy_tlt_momentum_spread_20d"] = (
            self.features["spy_momentum_20d"] - self.features["tlt_momentum_20d"]
        )

        self.features["equity_bond_corr_20d"] = (
            self.return_matrix["SPY"]
            .rolling(window=20)
            .corr(self.return_matrix["TLT"])
        )

        self.features["equity_gold_corr_20d"] = (
            self.return_matrix["SPY"]
            .rolling(window=20)
            .corr(self.return_matrix["GLD"])
        )

        self.features["risk_asset_dispersion_20d"] = (
            self.return_matrix[["SPY", "QQQ", "BTC-USD", "ETH-USD"]]
            .rolling(window=20)
            .std()
            .mean(axis=1)
        )

        logger.info(
            "Cross-asset feature preview:\n%s",
            self.features[
                [
                    "spy_tlt_momentum_spread_20d",
                    "equity_bond_corr_20d",
                    "equity_gold_corr_20d",
                    "risk_asset_dispersion_20d",
                ]
            ].tail().round(4),
        )

    def build_macro_proxy_features(self):
        logger.info("Building macro proxy features.")

        # Yield-spread proxy:
        # When direct yield curve data is unavailable, use equity-vs-duration bond momentum
        # as a market-implied growth/rate stress proxy.
        self.features["yield_spread_proxy"] = (
            self.features["spy_momentum_20d"] - self.features["tlt_momentum_20d"]
        )

        # VIX term-structure proxy:
        # Direct front/back VIX futures are unavailable, so use VIX spot versus moving average.
        # Above 1 = spot stress above recent normal.
        self.features["vix_term_structure_proxy"] = (
            self.features["vix_level"] / self.features["vix_ma_20d"]
        )

        # Inflation proxy:
        # GLD strength relative to TLT weakness can proxy inflation/rate pressure.
        self.features["inflation_pressure_proxy"] = (
            self.features["gld_momentum_20d"] - self.features["tlt_momentum_20d"]
        )

        # Liquidity proxy:
        # Falling equities + rising VIX implies liquidity stress.
        self.features["liquidity_stress_proxy"] = (
            self.features["vix_stress_ratio"]
            - self.features["spy_momentum_20d"]
        )

        logger.info(
            "Macro proxy preview:\n%s",
            self.features[
                [
                    "yield_spread_proxy",
                    "vix_term_structure_proxy",
                    "inflation_pressure_proxy",
                    "liquidity_stress_proxy",
                ]
            ].tail().round(4),
        )

    def build_volatility_regime_features(self):
        logger.info("Building volatility regime score.")

        rolling_spy_vol_mean = self.features["spy_vol_20d"].rolling(window=60).mean()
        rolling_vix_mean = self.features["vix_level"].rolling(window=60).mean()
        rolling_dispersion_mean = self.features["risk_asset_dispersion_20d"].rolling(window=60).mean()

        self.features["realized_vol_regime_score"] = (
            0.40 * (self.features["spy_vol_20d"] / rolling_spy_vol_mean)
            + 0.40 * (self.features["vix_level"] / rolling_vix_mean)
            + 0.20 * (
                self.features["risk_asset_dispersion_20d"] / rolling_dispersion_mean
            )
        )

        self.features["volatility_regime_label"] = pd.cut(
            self.features["realized_vol_regime_score"],
            bins=[-float("inf"), 0.90, 1.20, float("inf")],
            labels=["low_volatility", "normal_volatility", "high_volatility"],
        )

        logger.info(
            "Volatility regime preview:\n%s",
            self.features[
                ["realized_vol_regime_score", "volatility_regime_label"]
            ].tail(),
        )

    def finalize_feature_set(self):
        logger.info("Finalizing feature dataset.")

        self.features = self.features.dropna()

        logger.info("Final feature dataset shape: %s", self.features.shape)
        logger.info("Final feature columns: %s", list(self.features.columns))
        logger.info("Final feature preview:\n%s", self.features.tail().round(4))

    def save_outputs(self):
        logger.info("Saving macro feature dataset.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.features.to_parquet(self.output_path)
        self.features.tail(50).to_csv(self.preview_path)
        self.features.describe().T.to_csv(self.summary_path)

        logger.info("Saved macro features to: %s", self.output_path)
        logger.info("Saved macro feature preview to: %s", self.preview_path)
        logger.info("Saved macro feature summary to: %s", self.summary_path)

    def run(self):
        logger.info("Starting Macro Feature Engine v2.")
        logger.info("Input directory: %s", self.input_dir)
        logger.info("Output path: %s", self.output_path)

        self.load_data()
        self.build_price_matrix()
        self.build_return_matrix()
        self.initialize_features()
        self.build_volatility_features()
        self.build_momentum_features()
        self.build_cross_asset_features()
        self.build_macro_proxy_features()
        self.build_volatility_regime_features()
        self.finalize_feature_set()
        self.save_outputs()

        logger.info("Macro Feature Engine v2 completed successfully.")


if __name__ == "__main__":
    engine = MacroFeatureEngine()
    engine.run()