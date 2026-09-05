from pathlib import Path
import logging

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


class BayesianRegimeUpdater:
    """
    Bayesian Regime Updater v2 for AURUM.

    Uses HMM filtered probabilities as priors and updates them using:
    - macro stress evidence
    - volatility regime evidence
    - momentum breadth evidence
    - liquidity stress evidence

    Produces:
    - posterior regime probabilities
    - Bayesian most-likely state
    - posterior entropy
    - confidence diagnostics
    """

    def __init__(self):
        self.hmm_probability_path = Path("data/regimes/hidden_markov_filtered_probabilities.csv")
        self.hmm_regime_path = Path("data/regimes/hidden_markov_regimes.csv")

        self.output_dir = Path("data/regimes")
        self.output_path = self.output_dir / "bayesian_regime_probabilities.csv"
        self.summary_path = self.output_dir / "bayesian_regime_summary.csv"
        self.diagnostics_path = self.output_dir / "bayesian_regime_diagnostics.csv"

    def load_inputs(self):
        logger.info("Loading HMM probabilities from: %s", self.hmm_probability_path)
        logger.info("Loading HMM regimes from: %s", self.hmm_regime_path)

        self.hmm_probs = pd.read_csv(self.hmm_probability_path)
        self.hmm_regimes = pd.read_csv(self.hmm_regime_path)

        self.hmm_probs["Date"] = pd.to_datetime(self.hmm_probs["Date"])
        self.hmm_regimes["Date"] = pd.to_datetime(self.hmm_regimes["Date"])

        logger.info("Loaded HMM probabilities shape: %s", self.hmm_probs.shape)
        logger.info("Loaded HMM regimes shape: %s", self.hmm_regimes.shape)

    def infer_state_roles(self):
        """
        Infer economic roles from HMM summary statistics rather than hardcoding labels.

        Highest realized volatility score = crisis/risk-off state.
        Lowest realized volatility score = stable state.
        Remaining state = transition/uncertain state.
        """
        logger.info("Inferring state economic roles.")

        state_summary = (
            self.hmm_regimes
            .groupby("hidden_state")
            .agg(
                avg_vol_score=("realized_vol_regime_score", "mean"),
                avg_momentum_breadth=("momentum_breadth", "mean"),
                avg_liquidity_stress=("liquidity_stress_proxy", "mean"),
                avg_vix=("vix_level", "mean"),
            )
            .reset_index()
        )

        crisis_state = int(
            state_summary.sort_values("avg_vol_score", ascending=False)
            .iloc[0]["hidden_state"]
        )

        stable_state = int(
            state_summary.sort_values("avg_vol_score", ascending=True)
            .iloc[0]["hidden_state"]
        )

        transition_state = int(
            set(state_summary["hidden_state"])
            .difference({crisis_state, stable_state})
            .pop()
        )

        self.state_roles = {
            "crisis": crisis_state,
            "stable": stable_state,
            "transition": transition_state,
        }

        self.state_role_summary = state_summary

        logger.info("State role summary:\n%s", state_summary.round(4))
        logger.info("Inferred state roles: %s", self.state_roles)

    def build_evidence_score(self):
        logger.info("Building Bayesian evidence scores.")

        df = self.hmm_regimes.copy()

        df["volatility_evidence"] = df["realized_vol_regime_score"]

        df["liquidity_evidence"] = (
            df["liquidity_stress_proxy"]
            / df["liquidity_stress_proxy"].rolling(window=60).mean()
        )

        df["liquidity_evidence"] = df["liquidity_evidence"].replace(
            [np.inf, -np.inf],
            np.nan,
        )

        df["negative_momentum_evidence"] = (1 - df["momentum_breadth"]).clip(0, 1)

        df["vix_evidence"] = df["vix_stress_ratio"]

        df["macro_stress_evidence"] = (
            0.35 * df["volatility_evidence"]
            + 0.25 * df["vix_evidence"]
            + 0.25 * df["liquidity_evidence"]
            + 0.15 * df["negative_momentum_evidence"]
        )

        df["macro_stress_evidence"] = df["macro_stress_evidence"].fillna(
            df["macro_stress_evidence"].median()
        )

        df["macro_stress_evidence"] = df["macro_stress_evidence"].clip(lower=0.05)

        self.evidence = df[
            [
                "Date",
                "volatility_evidence",
                "vix_evidence",
                "liquidity_evidence",
                "negative_momentum_evidence",
                "macro_stress_evidence",
            ]
        ]

        logger.info("Evidence preview:\n%s", self.evidence.tail())

    def update_probabilities(self):
        logger.info("Updating HMM priors into Bayesian posteriors.")

        df = self.hmm_probs.merge(self.evidence, on="Date", how="inner")

        prior_cols = [
            col for col in df.columns
            if col.startswith("state_") and col.endswith("_filtered_probability")
        ]

        crisis_state = self.state_roles["crisis"]
        stable_state = self.state_roles["stable"]
        transition_state = self.state_roles["transition"]

        df[f"state_{crisis_state}_likelihood"] = df["macro_stress_evidence"]
        df[f"state_{stable_state}_likelihood"] = 1 / df["macro_stress_evidence"]
        df[f"state_{transition_state}_likelihood"] = (
            1 + (df["macro_stress_evidence"] - 1).abs()
        )

        for col in prior_cols:
            state_id = int(
                col.replace("state_", "").replace("_filtered_probability", "")
            )
            likelihood_col = f"state_{state_id}_likelihood"
            posterior_col = f"posterior_state_{state_id}_probability"

            df[posterior_col] = df[col] * df[likelihood_col]

        posterior_cols = [
            col for col in df.columns if col.startswith("posterior_state_")
        ]

        posterior_sum = df[posterior_cols].sum(axis=1).replace(0, np.nan)

        for col in posterior_cols:
            df[col] = df[col] / posterior_sum

        df[posterior_cols] = df[posterior_cols].fillna(1 / len(posterior_cols))

        df["bayesian_most_likely_state"] = (
            df[posterior_cols]
            .idxmax(axis=1)
            .str.extract(r"posterior_state_(\d+)_probability")
            .astype(int)
        )

        prob_clip = df[posterior_cols].clip(lower=1e-12)
        entropy = -(prob_clip * np.log(prob_clip)).sum(axis=1)
        max_entropy = np.log(len(posterior_cols))

        df["posterior_entropy"] = entropy
        df["posterior_normalized_entropy"] = entropy / max_entropy
        df["bayesian_confidence"] = 1 - df["posterior_normalized_entropy"]

        keep_cols = (
            ["Date"]
            + prior_cols
            + [
                "macro_stress_evidence",
                f"state_{crisis_state}_likelihood",
                f"state_{stable_state}_likelihood",
                f"state_{transition_state}_likelihood",
            ]
            + posterior_cols
            + [
                "bayesian_most_likely_state",
                "posterior_entropy",
                "posterior_normalized_entropy",
                "bayesian_confidence",
            ]
        )

        self.posterior = df[keep_cols]

        logger.info("Posterior probability preview:\n%s", self.posterior.tail())

    def build_summary(self):
        logger.info("Building Bayesian regime summary.")

        posterior_cols = [
            col for col in self.posterior.columns
            if col.startswith("posterior_state_")
        ]

        summary_rows = []

        for col in posterior_cols:
            state_id = int(
                col.replace("posterior_state_", "").replace("_probability", "")
            )

            role = None
            for role_name, role_state in self.state_roles.items():
                if role_state == state_id:
                    role = role_name

            summary_rows.append(
                {
                    "state": state_id,
                    "inferred_role": role,
                    "avg_posterior_probability": self.posterior[col].mean(),
                    "max_posterior_probability": self.posterior[col].max(),
                    "min_posterior_probability": self.posterior[col].min(),
                }
            )

        self.summary = pd.DataFrame(summary_rows)
        self.summary["avg_bayesian_confidence"] = self.posterior["bayesian_confidence"].mean()
        self.summary["avg_posterior_entropy"] = self.posterior["posterior_entropy"].mean()

        logger.info("Bayesian summary:\n%s", self.summary.round(4))

    def build_diagnostics(self):
        logger.info("Building Bayesian diagnostics.")

        role_rows = []

        for role, state in self.state_roles.items():
            role_rows.append(
                {
                    "role": role,
                    "state": state,
                }
            )

        self.diagnostics = pd.DataFrame(role_rows)

        logger.info("Bayesian diagnostics:\n%s", self.diagnostics)

    def save_outputs(self):
        logger.info("Saving Bayesian regime outputs.")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.posterior.to_csv(self.output_path, index=False)
        self.summary.to_csv(self.summary_path, index=False)
        self.diagnostics.to_csv(self.diagnostics_path, index=False)

        logger.info("Saved Bayesian regime probabilities to: %s", self.output_path)
        logger.info("Saved Bayesian summary to: %s", self.summary_path)
        logger.info("Saved Bayesian diagnostics to: %s", self.diagnostics_path)

    def run(self):
        logger.info("Starting Bayesian Regime Updater v2.")

        self.load_inputs()
        self.infer_state_roles()
        self.build_evidence_score()
        self.update_probabilities()
        self.build_summary()
        self.build_diagnostics()
        self.save_outputs()

        logger.info("Bayesian Regime Updater v2 completed successfully.")


if __name__ == "__main__":
    updater = BayesianRegimeUpdater()
    updater.run()