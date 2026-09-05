# src/digital_twin/regime_transition_simulator.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


TRANSITION_CANDIDATES = [
    Path("data/regimes/hidden_markov_transition_matrix.csv"),
    Path("data/regimes/regime_transition_matrix.csv"),
]

FORECAST_CANDIDATES = [
    Path("data/regimes/next_regime_forecast.csv"),
    Path("data/regimes/market_regimes.csv"),
]

OUTPUT_DIR = Path("results/digital_twin/regime_transition")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class RegimeForecast:
    current_regime: str
    next_regime: str
    probability: float


@dataclass
class RegimeSimulationSummary:
    current_regime: str
    most_likely_next_regime: str
    transition_probability: float
    panic_probability: float
    recovery_probability: float
    risk_off_probability: float
    risk_on_probability: float
    stability_score: float
    regime_risk_level: str


class RegimeTransitionSimulator:
    def load_transition_matrix(self) -> pd.DataFrame:
        for path in TRANSITION_CANDIDATES:
            if path.exists():
                print(f"[INFO] Using transition matrix: {path}")
                return pd.read_csv(path, index_col=0)

        raise FileNotFoundError(
            "No regime transition matrix found."
        )

    def infer_current_regime(self) -> str:
        for path in FORECAST_CANDIDATES:
            if not path.exists():
                continue

            try:
                df = pd.read_csv(path)

                possible_cols = [
                    "regime",
                    "current_regime",
                    "predicted_regime",
                    "forecast_regime",
                ]

                for col in possible_cols:
                    if col in df.columns:
                        value = str(df[col].iloc[-1])
                        print(f"[INFO] Current regime: {value}")
                        return value

            except Exception:
                pass

        return "normal"

    def normalize_labels(
        self,
        transition_matrix: pd.DataFrame,
    ) -> pd.DataFrame:
        df = transition_matrix.copy()

        df.index = [str(x).strip().lower() for x in df.index]
        df.columns = [str(x).strip().lower() for x in df.columns]

        return df

    def classify_probability(
        self,
        row: pd.Series,
        keywords: List[str],
    ) -> float:
        probability = 0.0

        for column in row.index:
            col = column.lower()

            if any(keyword in col for keyword in keywords):
                probability += float(row[column])

        return probability

    def classify_risk_level(
        self,
        panic_probability: float,
        risk_off_probability: float,
    ) -> str:
        risk_score = panic_probability + risk_off_probability

        if risk_score > 0.50:
            return "HIGH"
        if risk_score > 0.25:
            return "MODERATE"
        return "LOW"

    def run_simulation(
        self,
        transition_matrix: pd.DataFrame,
        current_regime: str,
    ) -> tuple[RegimeSimulationSummary, List[RegimeForecast]]:

        current_regime = current_regime.lower().strip()

        if current_regime not in transition_matrix.index:
            current_regime = transition_matrix.index[0]

        row = transition_matrix.loc[current_regime]

        forecasts: List[RegimeForecast] = []

        for next_regime, probability in row.items():
            forecasts.append(
                RegimeForecast(
                    current_regime=current_regime,
                    next_regime=str(next_regime),
                    probability=float(probability),
                )
            )

        forecasts = sorted(
            forecasts,
            key=lambda x: x.probability,
            reverse=True,
        )

        most_likely = forecasts[0]

        panic_probability = self.classify_probability(
            row,
            ["panic", "crisis", "stress"],
        )

        recovery_probability = self.classify_probability(
            row,
            ["recovery", "bull"],
        )

        risk_off_probability = self.classify_probability(
            row,
            ["risk_off", "bear", "defensive"],
        )

        risk_on_probability = self.classify_probability(
            row,
            ["risk_on", "normal", "bull"],
        )

        summary = RegimeSimulationSummary(
            current_regime=current_regime,
            most_likely_next_regime=most_likely.next_regime,
            transition_probability=most_likely.probability,
            panic_probability=panic_probability,
            recovery_probability=recovery_probability,
            risk_off_probability=risk_off_probability,
            risk_on_probability=risk_on_probability,
            stability_score=float(row.max()),
            regime_risk_level=self.classify_risk_level(
                panic_probability,
                risk_off_probability,
            ),
        )

        return summary, forecasts

    def write_outputs(
        self,
        summary: RegimeSimulationSummary,
        forecasts: List[RegimeForecast],
    ) -> None:

        summary_path = OUTPUT_DIR / "regime_transition_summary.json"
        forecast_path = OUTPUT_DIR / "regime_transition_forecasts.csv"
        report_path = OUTPUT_DIR / "regime_transition_report.txt"

        summary_path.write_text(
            json.dumps(asdict(summary), indent=2),
            encoding="utf-8",
        )

        pd.DataFrame(
            [asdict(x) for x in forecasts]
        ).to_csv(
            forecast_path,
            index=False,
        )

        lines = [
            "=" * 80,
            "AURUM REGIME TRANSITION SIMULATOR",
            "=" * 80,
            "",
            f"Current Regime: {summary.current_regime}",
            f"Most Likely Next Regime: {summary.most_likely_next_regime}",
            f"Transition Probability: {summary.transition_probability:.4f}",
            "",
            f"Risk-On Probability: {summary.risk_on_probability:.4f}",
            f"Risk-Off Probability: {summary.risk_off_probability:.4f}",
            f"Panic Probability: {summary.panic_probability:.4f}",
            f"Recovery Probability: {summary.recovery_probability:.4f}",
            "",
            f"Stability Score: {summary.stability_score:.4f}",
            f"Regime Risk Level: {summary.regime_risk_level}",
        ]

        report_path.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

    def print_results(
        self,
        summary: RegimeSimulationSummary,
        forecasts: List[RegimeForecast],
    ) -> None:

        print("=" * 80)
        print("AURUM REGIME TRANSITION SIMULATOR")
        print("=" * 80)

        print(f"Current Regime: {summary.current_regime}")
        print(f"Most Likely Next: {summary.most_likely_next_regime}")
        print(f"Transition Probability: {summary.transition_probability:.4f}")
        print("-" * 80)

        for forecast in forecasts:
            print(
                f"{forecast.next_regime:<20}"
                f"{forecast.probability:.4f}"
            )

        print("-" * 80)
        print(f"Risk Level: {summary.regime_risk_level}")

    def run(self) -> None:

        transition_matrix = self.load_transition_matrix()
        transition_matrix = self.normalize_labels(
            transition_matrix
        )

        current_regime = self.infer_current_regime()

        summary, forecasts = self.run_simulation(
            transition_matrix,
            current_regime,
        )

        self.write_outputs(
            summary,
            forecasts,
        )

        self.print_results(
            summary,
            forecasts,
        )


def main() -> None:
    simulator = RegimeTransitionSimulator()
    simulator.run()


if __name__ == "__main__":
    main()