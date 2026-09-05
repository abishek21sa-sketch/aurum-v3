from pathlib import Path
import logging

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class EnsembleForecastEngine:
    """
    Ensemble Forecast Engine v2 for AURUM.

    Combines:
    - cross-sectional alpha
    - calibrated regime probabilities
    - macro stress
    - tail-risk controls
    - dynamic hedge posture

    Produces:
    - final_expected_return_signal
    - forecast conviction
    - uncertainty-adjusted allocation preference
    """

    def __init__(self):
        self.alpha_path = Path("data/signals/cross_sectional_alpha_signals.csv")
        self.regime_path = Path("data/regimes/calibrated_regime_probabilities.csv")
        self.hedge_path = Path("data/risk/dynamic_hedging_policy.csv")
        self.tail_risk_path = Path("data/risk/asset_tail_risk_report.csv")
        self.macro_path = Path("data/features/macro_features.parquet")

        self.output_dir = Path("data/forecasting")
        self.signal_path = self.output_dir / "ensemble_forecast_signals.csv"
        self.summary_path = self.output_dir / "ensemble_forecast_summary.csv"

    def load_inputs(self):
        logger.info("Loading alpha signals from: %s", self.alpha_path)
        logger.info("Loading regimes from: %s", self.regime_path)
        logger.info("Loading hedging policy from: %s", self.hedge_path)
        logger.info("Loading asset tail risk from: %s", self.tail_risk_path)
        logger.info("Loading macro features from: %s", self.macro_path)

        self.alpha = pd.read_csv(self.alpha_path)
        self.regimes = pd.read_csv(self.regime_path)
        self.hedges = pd.read_csv(self.hedge_path)
        self.tail_risk = pd.read_csv(self.tail_risk_path)
        self.macro = pd.read_parquet(self.macro_path).reset_index()

        self.alpha["Date"] = pd.to_datetime(self.alpha["Date"])
        self.regimes["Date"] = pd.to_datetime(self.regimes["Date"])
        self.hedges["Date"] = pd.to_datetime(self.hedges["Date"])
        self.macro["Date"] = pd.to_datetime(self.macro["Date"])

        logger.info("Loaded alpha shape: %s", self.alpha.shape)
        logger.info("Loaded regimes shape: %s", self.regimes.shape)
        logger.info("Loaded hedges shape: %s", self.hedges.shape)
        logger.info("Loaded tail risk shape: %s", self.tail_risk.shape)
        logger.info("Loaded macro shape: %s", self.macro.shape)

    def build_forecast_dataset(self):
        logger.info("Building ensemble forecast dataset.")

        regime_cols = [
            "Date",
            "calibrated_state_0_probability",
            "calibrated_state_1_probability",
            "calibrated_state_2_probability",
            "calibrated_most_likely_state",
            "calibrated_regime_confidence",
            "calibrated_max_probability",
        ]

        hedge_cols = [
            "Date",
            "equity_exposure",
            "bond_hedge_exposure",
            "gold_hedge_exposure",
            "cash_buffer",
            "hedge_intensity",
            "hedging_regime_label",
        ]

        macro_cols = [
            "Date",
            "vix_stress_ratio",
            "liquidity_stress_proxy",
            "momentum_breadth",
            "realized_vol_regime_score",
        ]

        tail_cols = [
            "asset",
            "cvar_95_expected_shortfall",
            "downside_semivariance",
            "max_drawdown",
            "volatility",
        ]

        df = self.alpha.copy()

        duplicate_regime_cols = [
            col for col in df.columns
            if col.startswith("calibrated_state_")
            or col in [
                "calibrated_most_likely_state",
                "calibrated_regime_confidence",
                "calibrated_max_probability",
            ]
        ]

        df = df.drop(columns=duplicate_regime_cols, errors="ignore")

        df = df.merge(
            self.regimes[regime_cols],
            on="Date",
            how="inner",
        )

        duplicate_hedge_cols = [
            col for col in df.columns
            if col in [
                "equity_exposure",
                "bond_hedge_exposure",
                "gold_hedge_exposure",
                "cash_buffer",
                "hedge_intensity",
                "hedging_regime_label",
            ]
        ]

        df = df.drop(columns=duplicate_hedge_cols, errors="ignore")

        df = df.merge(
            self.hedges[hedge_cols],
            on="Date",
            how="inner",
        )

        duplicate_macro_cols = [
            col for col in df.columns
            if col in [
                "vix_stress_ratio",
                "liquidity_stress_proxy",
                "momentum_breadth",
                "realized_vol_regime_score",
            ]
        ]

        df = df.drop(columns=duplicate_macro_cols, errors="ignore")

        df = df.merge(
            self.macro[macro_cols],
            on="Date",
            how="inner",
        )

        df = df.merge(
            self.tail_risk[tail_cols],
            on="asset",
            how="left",
        )

        self.forecast_data = df

        logger.info("Forecast dataset shape: %s", self.forecast_data.shape)
        logger.info("Forecast dataset columns: %s", list(self.forecast_data.columns))
        logger.info("Forecast dataset preview:\n%s", self.forecast_data.tail())

    def compute_forecast_components(self):
        logger.info("Computing forecast components.")

        df = self.forecast_data.copy()

        risk_assets = {"SPY", "QQQ", "DIA", "BTC-USD", "ETH-USD"}
        defensive_assets = {"TLT", "GLD", "VIX"}

        df["factor_component"] = df["regime_adjusted_alpha"]

        df["regime_component"] = (
            0.55 * df["calibrated_state_1_probability"]
            + 0.25 * df["calibrated_state_2_probability"]
            - 0.35 * df["calibrated_state_0_probability"]
        )

        df.loc[df["asset"].isin(defensive_assets), "regime_component"] = (
            0.45 * df["calibrated_state_0_probability"]
            + 0.25 * df["calibrated_state_2_probability"]
            - 0.15 * df["calibrated_state_1_probability"]
        )

        df["macro_component"] = (
            0.40 * df["momentum_breadth"]
            - 0.30 * df["realized_vol_regime_score"]
            - 0.20 * df["liquidity_stress_proxy"]
            - 0.10 * df["vix_stress_ratio"]
        )

        df.loc[df["asset"].isin(defensive_assets), "macro_component"] = (
            0.30 * df["realized_vol_regime_score"]
            + 0.25 * df["liquidity_stress_proxy"]
            + 0.20 * df["vix_stress_ratio"]
            - 0.15 * df["momentum_breadth"]
        )

        df["risk_penalty"] = (
            df["cvar_95_expected_shortfall"].abs()
            + df["downside_semivariance"].fillna(0)
            + df["max_drawdown"].abs()
        )

        df["risk_penalty_scaled"] = (
            df.groupby("Date")["risk_penalty"]
            .transform(
                lambda x: (
                    (x - x.min()) / (x.max() - x.min())
                    if x.max() != x.min()
                    else 0
                )
            )
        )

        df["hedge_alignment_component"] = 0.0

        df.loc[df["asset"].isin(risk_assets), "hedge_alignment_component"] = (
            df["equity_exposure"]
        )

        df.loc[df["asset"] == "TLT", "hedge_alignment_component"] = (
            df["bond_hedge_exposure"]
        )

        df.loc[df["asset"] == "GLD", "hedge_alignment_component"] = (
            df["gold_hedge_exposure"]
        )

        df.loc[df["asset"] == "VIX", "hedge_alignment_component"] = (
            df["hedge_intensity"]
        )

        self.forecast_components = df

    def compute_final_signal(self):
        logger.info("Computing final ensemble forecast signal.")

        df = self.forecast_components.copy()

        df["final_expected_return_signal"] = (
            0.45 * df["factor_component"]
            + 0.25 * df["regime_component"]
            + 0.15 * df["macro_component"]
            + 0.15 * df["hedge_alignment_component"]
            - 0.25 * df["risk_penalty_scaled"]
        )

        df["forecast_uncertainty"] = (
            1 - df["calibrated_max_probability"]
        )

        df["forecast_conviction"] = (
            df["calibrated_max_probability"]
            * (1 - df["risk_penalty_scaled"] * 0.35)
        ).clip(lower=0, upper=1)

        df["uncertainty_adjusted_signal"] = (
            df["final_expected_return_signal"]
            * df["forecast_conviction"]
        )

        df["allocation_preference_rank"] = (
            df.groupby("Date")["uncertainty_adjusted_signal"]
            .rank(ascending=False, pct=True)
        )

        self.forecast = df

        logger.info("Forecast preview:\n%s", self.forecast.tail())

    def build_summary(self):
        logger.info("Building ensemble forecast summary.")

        self.summary = (
            self.forecast
            .groupby("asset")
            .agg(
                observations=("asset", "count"),
                avg_final_expected_return_signal=("final_expected_return_signal", "mean"),
                avg_uncertainty_adjusted_signal=("uncertainty_adjusted_signal", "mean"),
                avg_forecast_conviction=("forecast_conviction", "mean"),
                avg_allocation_preference_rank=("allocation_preference_rank", "mean"),
                avg_risk_penalty_scaled=("risk_penalty_scaled", "mean"),
            )
            .reset_index()
            .sort_values("avg_uncertainty_adjusted_signal", ascending=False)
        )

        logger.info("Ensemble forecast summary:\n%s", self.summary.round(4))

    def save_outputs(self):
        logger.info("Saving ensemble forecast outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.forecast.to_csv(self.signal_path, index=False)
        self.summary.to_csv(self.summary_path, index=False)

        logger.info("Saved ensemble forecast signals to: %s", self.signal_path)
        logger.info("Saved ensemble forecast summary to: %s", self.summary_path)

    def run(self):
        logger.info("Starting Ensemble Forecast Engine v2.")

        self.load_inputs()
        self.build_forecast_dataset()
        self.compute_forecast_components()
        self.compute_final_signal()
        self.build_summary()
        self.save_outputs()

        logger.info("Ensemble Forecast Engine v2 completed successfully.")


if __name__ == "__main__":
    engine = EnsembleForecastEngine()
    engine.run()