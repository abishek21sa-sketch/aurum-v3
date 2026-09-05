from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


INPUT_DIR = Path("results/regime_intelligence")
OUTPUT_DIR = Path("results/regime_intelligence")

TRANSITION_DECISION_PATH = INPUT_DIR / "transition_decision.json"
CONFIDENCE_SUMMARY_PATH = INPUT_DIR / "confidence_exposure_summary.json"
OUTPUT_PATH = OUTPUT_DIR / "dynamic_hedge_overlay.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_latest_volatility_signal() -> float:
    candidates = [
        Path("data/forecasting/volatility_forecasts.csv"),
        Path("data/features/macro_features_preview.csv"),
    ]

    for path in candidates:
        if not path.exists():
            continue

        df = pd.read_csv(path)

        possible_cols = [
            "forecast_volatility",
            "volatility_forecast",
            "SPY_vol_20d",
            "spy_vol_20d",
            "portfolio_volatility",
        ]

        for col in possible_cols:
            if col in df.columns and len(df) > 0:
                try:
                    return float(df.iloc[-1][col])
                except (TypeError, ValueError):
                    continue

    return 0.15


def classify_volatility(volatility: float) -> str:
    if volatility >= 0.30:
        return "extreme"
    if volatility >= 0.22:
        return "high"
    if volatility >= 0.14:
        return "moderate"
    return "low"


def build_overlay_weights(
    regime: str,
    volatility_label: str,
    crisis_probability: float,
    transition_risk: str,
) -> dict:
    overlay = {
        "SPY": 0.0,
        "QQQ": 0.0,
        "DIA": 0.0,
        "TLT": 0.0,
        "GLD": 0.0,
        "VIX": 0.0,
        "BTC-USD": 0.0,
        "ETH-USD": 0.0,
        "CASH": 0.0,
    }

    if regime == "bull":
        overlay["VIX"] += 0.01
        overlay["CASH"] += 0.01

    elif regime == "normal":
        overlay["TLT"] += 0.02
        overlay["GLD"] += 0.01
        overlay["CASH"] += 0.01

    elif regime == "high_volatility":
        overlay["VIX"] += 0.05
        overlay["TLT"] += 0.04
        overlay["GLD"] += 0.03
        overlay["CASH"] += 0.04

    elif regime == "risk_off":
        overlay["TLT"] += 0.06
        overlay["GLD"] += 0.05
        overlay["VIX"] += 0.04
        overlay["CASH"] += 0.06

    elif regime == "liquidity_stress":
        overlay["CASH"] += 0.10
        overlay["TLT"] += 0.06
        overlay["GLD"] += 0.04
        overlay["VIX"] += 0.04

    elif regime == "crisis":
        overlay["CASH"] += 0.12
        overlay["TLT"] += 0.08
        overlay["GLD"] += 0.06
        overlay["VIX"] += 0.08

    if volatility_label in {"high", "extreme"}:
        overlay["VIX"] += 0.03
        overlay["CASH"] += 0.02

    if crisis_probability >= 0.25:
        overlay["TLT"] += 0.04
        overlay["GLD"] += 0.04
        overlay["CASH"] += 0.04
        overlay["VIX"] += 0.03

    if transition_risk == "high":
        overlay["CASH"] += 0.04
        overlay["TLT"] += 0.02

    total_overlay = sum(overlay.values())

    if total_overlay > 0.35:
        scale = 0.35 / total_overlay
        overlay = {asset: weight * scale for asset, weight in overlay.items()}

    return {asset: round(weight, 6) for asset, weight in overlay.items()}


def determine_hedge_status(overlay_weights: dict) -> str:
    total_overlay = sum(overlay_weights.values())

    if total_overlay >= 0.20:
        return "active_heavy"
    if total_overlay >= 0.08:
        return "active_moderate"
    if total_overlay > 0:
        return "active_light"
    return "inactive"


def build_dynamic_hedge_overlay() -> dict:
    transition = load_json(TRANSITION_DECISION_PATH)
    confidence = load_json(CONFIDENCE_SUMMARY_PATH)

    regime = transition["effective_allocation_regime"]
    transition_risk = transition["transition_risk_label"]
    probabilities = transition.get("regime_probabilities", {})

    crisis_probability = float(probabilities.get("crisis", 0.0))
    volatility = get_latest_volatility_signal()
    volatility_label = classify_volatility(volatility)

    overlay_weights = build_overlay_weights(
        regime=regime,
        volatility_label=volatility_label,
        crisis_probability=crisis_probability,
        transition_risk=transition_risk,
    )

    hedge_status = determine_hedge_status(overlay_weights)

    return {
        "module": "dynamic_hedge_overlay_engine",
        "effective_regime": regime,
        "transition_risk_label": transition_risk,
        "combined_confidence": confidence["combined_confidence"],
        "volatility_signal": round(float(volatility), 6),
        "volatility_label": volatility_label,
        "crisis_probability": round(crisis_probability, 6),
        "hedge_status": hedge_status,
        "overlay_weights": overlay_weights,
        "total_overlay_weight": round(sum(overlay_weights.values()), 6),
        "interpretation": (
            "The hedge overlay adds defensive exposure based on regime, volatility, "
            "crisis probability, and transition risk. The final switch engine will fund "
            "this overlay by proportionally reducing risky assets."
        ),
    }


def save_overlay(overlay: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(overlay, indent=4), encoding="utf-8")


def main() -> None:
    overlay = build_dynamic_hedge_overlay()
    save_overlay(overlay)

    print("=" * 80)
    print("AURUM DYNAMIC HEDGE OVERLAY ENGINE")
    print("=" * 80)
    print(f"Effective Regime:      {overlay['effective_regime']}")
    print(f"Transition Risk:       {overlay['transition_risk_label']}")
    print(f"Volatility Signal:     {overlay['volatility_signal']}")
    print(f"Volatility Label:      {overlay['volatility_label']}")
    print(f"Crisis Probability:    {overlay['crisis_probability']}")
    print(f"Hedge Status:          {overlay['hedge_status']}")
    print(f"Total Overlay Weight:  {overlay['total_overlay_weight']}")
    print()
    for asset, weight in overlay["overlay_weights"].items():
        if weight > 0:
            print(f"{asset:10s} +{weight:.4f}")
    print()
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()