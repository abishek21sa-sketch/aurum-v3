from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import pandas as pd


DATA_REGIME_DIR = Path("data/regimes")
OUTPUT_DIR = Path("results/regime_intelligence")
OUTPUT_PATH = OUTPUT_DIR / "transition_decision.json"


REGIME_ORDER = {
    "bull": 0,
    "normal": 1,
    "high_volatility": 2,
    "risk_off": 3,
    "liquidity_stress": 4,
    "crisis": 5,
}


def normalize_regime_name(regime: str) -> str:
    return str(regime).strip().lower().replace(" ", "_")


def load_latest_market_regime() -> tuple[str, str]:
    path = DATA_REGIME_DIR / "market_regimes.csv"

    if not path.exists():
        return "normal", "normal"

    df = pd.read_csv(path)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")

    if "regime" not in df.columns or len(df) == 0:
        return "normal", "normal"

    current_regime = normalize_regime_name(df.iloc[-1]["regime"])
    previous_regime = normalize_regime_name(df.iloc[-2]["regime"]) if len(df) >= 2 else current_regime

    return previous_regime, current_regime


def load_regime_probabilities() -> Dict[str, float]:
    candidate_files = [
        DATA_REGIME_DIR / "calibrated_regime_probabilities.csv",
        DATA_REGIME_DIR / "bayesian_regime_probabilities.csv",
        DATA_REGIME_DIR / "hidden_markov_probabilities.csv",
    ]

    for path in candidate_files:
        if not path.exists():
            continue

        df = pd.read_csv(path)

        if len(df) == 0:
            continue

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date")

        latest = df.iloc[-1].to_dict()

        probabilities = {}
        for key, value in latest.items():
            clean_key = normalize_regime_name(key)

            if clean_key in REGIME_ORDER:
                try:
                    probabilities[clean_key] = float(value)
                except (TypeError, ValueError):
                    pass

        total = sum(probabilities.values())

        if total > 0:
            return {k: v / total for k, v in probabilities.items()}

    return {"normal": 1.0}


def load_transition_matrix() -> Optional[pd.DataFrame]:
    path = DATA_REGIME_DIR / "regime_transition_matrix.csv"

    if not path.exists():
        return None

    matrix = pd.read_csv(path, index_col=0)
    matrix.index = [normalize_regime_name(x) for x in matrix.index]
    matrix.columns = [normalize_regime_name(x) for x in matrix.columns]

    return matrix


def classify_transition_risk(
    previous_regime: str,
    current_regime: str,
    probabilities: Dict[str, float],
    transition_matrix: Optional[pd.DataFrame],
) -> tuple[str, float]:
    previous_score = REGIME_ORDER.get(previous_regime, 1)
    current_score = REGIME_ORDER.get(current_regime, 1)

    jump_size = abs(current_score - previous_score)
    crisis_probability = probabilities.get("crisis", 0.0)
    stress_probability = probabilities.get("liquidity_stress", 0.0)
    risk_off_probability = probabilities.get("risk_off", 0.0)

    historical_probability = 0.0
    if transition_matrix is not None:
        if previous_regime in transition_matrix.index and current_regime in transition_matrix.columns:
            historical_probability = float(transition_matrix.loc[previous_regime, current_regime])

    risk_score = (
        0.35 * min(jump_size / 3.0, 1.0)
        + 0.25 * crisis_probability
        + 0.20 * stress_probability
        + 0.10 * risk_off_probability
        + 0.10 * (1.0 - historical_probability)
    )

    if risk_score >= 0.65:
        label = "high"
    elif risk_score >= 0.35:
        label = "moderate"
    else:
        label = "low"

    return label, round(risk_score, 4)


def select_effective_regime(
    previous_regime: str,
    current_regime: str,
    transition_risk_label: str,
) -> str:
    previous_score = REGIME_ORDER.get(previous_regime, 1)
    current_score = REGIME_ORDER.get(current_regime, 1)

    jump_size = current_score - previous_score

    if abs(jump_size) <= 1:
        return current_regime

    if transition_risk_label == "high":
        if jump_size > 0:
            intermediate_score = previous_score + 1
        else:
            intermediate_score = previous_score - 1

        for regime, score in REGIME_ORDER.items():
            if score == intermediate_score:
                return regime

    return current_regime


def build_transition_decision() -> dict:
    previous_regime, current_regime = load_latest_market_regime()
    probabilities = load_regime_probabilities()
    transition_matrix = load_transition_matrix()

    transition_risk_label, transition_risk_score = classify_transition_risk(
        previous_regime=previous_regime,
        current_regime=current_regime,
        probabilities=probabilities,
        transition_matrix=transition_matrix,
    )

    effective_regime = select_effective_regime(
        previous_regime=previous_regime,
        current_regime=current_regime,
        transition_risk_label=transition_risk_label,
    )

    regime_confidence = max(probabilities.values()) if probabilities else 1.0

    return {
        "module": "regime_transition_decision_engine",
        "purpose": "Convert detected regime movement into a stable allocation regime for AURUM Chat 3C.",
        "previous_regime": previous_regime,
        "detected_current_regime": current_regime,
        "effective_allocation_regime": effective_regime,
        "transition_risk_label": transition_risk_label,
        "transition_risk_score": transition_risk_score,
        "regime_confidence": round(float(regime_confidence), 4),
        "regime_probabilities": probabilities,
        "decision_rule": (
            "Large jumps are staged through adjacent regimes when transition risk is high. "
            "This prevents unstable allocation flips such as bull directly to crisis."
        ),
    }


def save_transition_decision(decision: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(decision, indent=4), encoding="utf-8")


def main() -> None:
    decision = build_transition_decision()
    save_transition_decision(decision)

    print("=" * 80)
    print("AURUM REGIME TRANSITION DECISION ENGINE")
    print("=" * 80)
    print(f"Previous Regime:          {decision['previous_regime']}")
    print(f"Detected Current Regime:  {decision['detected_current_regime']}")
    print(f"Effective Regime:         {decision['effective_allocation_regime']}")
    print(f"Transition Risk:          {decision['transition_risk_label']} ({decision['transition_risk_score']})")
    print(f"Regime Confidence:        {decision['regime_confidence']}")
    print()
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()