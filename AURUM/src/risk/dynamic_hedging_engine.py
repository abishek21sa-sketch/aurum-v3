from pathlib import Path
import logging

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class DynamicHedgingEngine:
    """
    Dynamic Hedging Engine v2 for AURUM.

    Adds:
    - regime-aware hedge allocation
    - volatility targeting
    - drawdown-sensitive de-risking
    - adaptive equity/bond/gold/cash posture
    """

    def __init__(self, target_volatility: float = 0.10):
        self.target_volatility = target_volatility

        self.regime_path = Path("data/regimes/calibrated_regime_probabilities.csv")
        self.macro_path = Path("data/features/macro_features.parquet")
        self.return_path = Path("data/market_matrix/market_return_matrix.csv")

        self.output_dir = Path("data/risk")
        self.output_path = self.output_dir / "dynamic_hedging_policy.csv"
        self.summary_path = self.output_dir / "dynamic_hedging_summary.csv"

    def load_inputs(self):
        logger.info("Loading calibrated regime probabilities from: %s", self.regime_path)
        logger.info("Loading macro features from: %s", self.macro_path)
        logger.info("Loading returns from: %s", self.return_path)

        self.regimes = pd.read_csv(self.regime_path)
        self.macro = pd.read_parquet(self.macro_path)
        self.returns = pd.read_csv(self.return_path)

        self.regimes["Date"] = pd.to_datetime(self.regimes["Date"])
        self.macro = self.macro.reset_index()
        self.macro["Date"] = pd.to_datetime(self.macro["Date"])
        self.returns["Date"] = pd.to_datetime(self.returns["Date"])

        logger.info("Loaded regime shape: %s", self.regimes.shape)
        logger.info("Loaded macro shape: %s", self.macro.shape)
        logger.info("Loaded returns shape: %s", self.returns.shape)

    def build_portfolio_state_features(self):
        logger.info("Building portfolio state features.")

        asset_cols = [col for col in self.returns.columns if col != "Date"]

        df = self.returns.copy()
        df["portfolio_return"] = df[asset_cols].fillna(0).mean(axis=1)

        df["cumulative_return"] = (1 + df["portfolio_return"]).cumprod()
        df["running_peak"] = df["cumulative_return"].cummax()
        df["drawdown"] = df["cumulative_return"] / df["running_peak"] - 1

        self.portfolio_state = df[
            ["Date", "portfolio_return", "cumulative_return", "drawdown"]
        ]

        logger.info(
            "Portfolio state preview:\n%s",
            self.portfolio_state.tail(),
        )

    def build_policy_dataset(self):
        logger.info("Building hedging policy dataset.")

        macro_cols = [
            "Date",
            "spy_vol_20d",
            "vix_level",
            "vix_stress_ratio",
            "realized_vol_regime_score",
            "liquidity_stress_proxy",
            "momentum_breadth",
        ]

        df = self.regimes.merge(
            self.macro[macro_cols],
            on="Date",
            how="inner",
        )

        df = df.merge(
            self.portfolio_state,
            on="Date",
            how="left",
        )

        df["drawdown"] = df["drawdown"].fillna(0)

        self.policy_data = df

        logger.info("Policy dataset shape: %s", self.policy_data.shape)

    def compute_base_regime_policy(self):
        logger.info("Computing base regime-aware hedge policy.")

        df = self.policy_data.copy()

        # State role after Bayesian v2 diagnostics:
        # state 0 = crisis
        # state 1 = stable
        # state 2 = transition
        crisis_prob = df["calibrated_state_0_probability"]
        stable_prob = df["calibrated_state_1_probability"]
        transition_prob = df["calibrated_state_2_probability"]

        df["base_equity_exposure"] = (
            0.80 * stable_prob
            + 0.45 * transition_prob
            + 0.20 * crisis_prob
        )

        df["base_bond_hedge_exposure"] = (
            0.15 * stable_prob
            + 0.30 * transition_prob
            + 0.45 * crisis_prob
        )

        df["base_gold_hedge_exposure"] = (
            0.03 * stable_prob
            + 0.15 * transition_prob
            + 0.20 * crisis_prob
        )

        df["base_cash_buffer"] = (
            0.02 * stable_prob
            + 0.10 * transition_prob
            + 0.15 * crisis_prob
        )

        self.policy_data = df

    def apply_volatility_targeting(self):
        logger.info("Applying volatility targeting.")

        df = self.policy_data.copy()

        df["volatility_scaler"] = (
            self.target_volatility / df["spy_vol_20d"]
        ).clip(lower=0.40, upper=1.25)

        df["vol_targeted_equity_exposure"] = (
            df["base_equity_exposure"] * df["volatility_scaler"]
        )

        equity_reduction = (
            df["base_equity_exposure"] - df["vol_targeted_equity_exposure"]
        ).clip(lower=0)

        df["vol_targeted_cash_buffer"] = (
            df["base_cash_buffer"] + equity_reduction
        )

        self.policy_data = df

    def apply_drawdown_derisking(self):
        logger.info("Applying drawdown-sensitive de-risking.")

        df = self.policy_data.copy()

        df["drawdown_derisking_multiplier"] = 1.0

        df.loc[df["drawdown"] <= -0.05, "drawdown_derisking_multiplier"] = 0.85
        df.loc[df["drawdown"] <= -0.10, "drawdown_derisking_multiplier"] = 0.70
        df.loc[df["drawdown"] <= -0.15, "drawdown_derisking_multiplier"] = 0.55

        df["equity_exposure"] = (
            df["vol_targeted_equity_exposure"]
            * df["drawdown_derisking_multiplier"]
        )

        equity_cut = (
            df["vol_targeted_equity_exposure"] - df["equity_exposure"]
        ).clip(lower=0)

        df["bond_hedge_exposure"] = df["base_bond_hedge_exposure"]
        df["gold_hedge_exposure"] = df["base_gold_hedge_exposure"]
        df["cash_buffer"] = df["vol_targeted_cash_buffer"] + equity_cut

        exposure_cols = [
            "equity_exposure",
            "bond_hedge_exposure",
            "gold_hedge_exposure",
            "cash_buffer",
        ]

        exposure_sum = df[exposure_cols].sum(axis=1)

        for col in exposure_cols:
            df[col] = df[col] / exposure_sum

        df["hedge_intensity"] = (
            df["bond_hedge_exposure"]
            + df["gold_hedge_exposure"]
            + df["cash_buffer"]
        )

        df["hedging_regime_label"] = pd.cut(
            df["hedge_intensity"],
            bins=[-0.01, 0.35, 0.55, 1.00],
            labels=[
                "low_hedge_stable",
                "moderate_hedge_uncertain",
                "high_hedge_risk_off",
            ],
        )

        self.policy = df[
            [
                "Date",
                "calibrated_state_0_probability",
                "calibrated_state_1_probability",
                "calibrated_state_2_probability",
                "calibrated_most_likely_state",
                "calibrated_regime_confidence",
                "spy_vol_20d",
                "vix_level",
                "realized_vol_regime_score",
                "liquidity_stress_proxy",
                "momentum_breadth",
                "drawdown",
                "volatility_scaler",
                "drawdown_derisking_multiplier",
                "equity_exposure",
                "bond_hedge_exposure",
                "gold_hedge_exposure",
                "cash_buffer",
                "hedge_intensity",
                "hedging_regime_label",
            ]
        ]

        logger.info(
            "Dynamic hedge policy preview:\n%s",
            self.policy.tail(),
        )

    def build_summary(self):
        logger.info("Building dynamic hedging summary.")

        self.summary = (
            self.policy
            .groupby("hedging_regime_label", observed=False)
            .agg(
                observations=("hedging_regime_label", "count"),
                avg_equity_exposure=("equity_exposure", "mean"),
                avg_bond_hedge_exposure=("bond_hedge_exposure", "mean"),
                avg_gold_hedge_exposure=("gold_hedge_exposure", "mean"),
                avg_cash_buffer=("cash_buffer", "mean"),
                avg_hedge_intensity=("hedge_intensity", "mean"),
                avg_volatility_scaler=("volatility_scaler", "mean"),
                avg_drawdown=("drawdown", "mean"),
                avg_derisking_multiplier=("drawdown_derisking_multiplier", "mean"),
                avg_regime_confidence=("calibrated_regime_confidence", "mean"),
            )
            .reset_index()
        )

        logger.info(
            "Dynamic hedging summary:\n%s",
            self.summary.round(4),
        )

    def save_outputs(self):
        logger.info("Saving dynamic hedging outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.policy.to_csv(self.output_path, index=False)
        self.summary.to_csv(self.summary_path, index=False)

        logger.info("Saved hedging policy to: %s", self.output_path)
        logger.info("Saved hedging summary to: %s", self.summary_path)

    def run(self):
        logger.info("Starting Dynamic Hedging Engine v2.")

        self.load_inputs()
        self.build_portfolio_state_features()
        self.build_policy_dataset()
        self.compute_base_regime_policy()
        self.apply_volatility_targeting()
        self.apply_drawdown_derisking()
        self.build_summary()
        self.save_outputs()

        logger.info("Dynamic Hedging Engine v2 completed successfully.")


if __name__ == "__main__":
    engine = DynamicHedgingEngine(target_volatility=0.10)
    engine.run()