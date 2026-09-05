from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd


INPUT_DIR = Path("results/regime_intelligence")
OUTPUT_DIR = Path("results/regime_intelligence")

PORTFOLIO_LIBRARY_PATH = INPUT_DIR / "regime_portfolio_library.json"
TRANSITION_DECISION_PATH = INPUT_DIR / "transition_decision.json"
OUTPUT_PATH = OUTPUT_DIR / "confidence_adjusted_portfolio.csv"
SUMMARY_PATH = OUTPUT_DIR / "confidence_exposure_summary.json"


RISK_ASSETS = ["SPY", "QQQ", "DIA", "BTC-USD", "ETH-USD"]
DEFENSIVE_ASSETS = ["TLT", "GLD", "VIX"]
CASH_ASSET = "CASH"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def get_signal_confidence() -> float:
    signal_path = Path("data/live/live_signal_snapshot.csv")

    if not signal_path.exists():
        return 0.70

    df = pd.read_csv(signal_path)

    confidence_columns = [
        "signal_confidence",
        "confidence",
        "market_signal_confidence",
    ]

    for col in confidence_columns:
        if col in df.columns and len(df) > 0:
            value = float(df.iloc[-1][col])
            return min(max(value, 0.0), 1.0)

    return 0.70


def get_forecast_confidence() -> float:
    forecast_path = Path("data/forecasting/ensemble_forecast_summary.csv")

    if not forecast_path.exists():
        return 0.70

    df = pd.read_csv(forecast_path)

    confidence_columns = [
        "forecast_confidence",
        "confidence",
        "ensemble_confidence",
    ]

    for col in confidence_columns:
        if col in df.columns and len(df) > 0:
            value = float(df.iloc[-1][col])
            return min(max(value, 0.0), 1.0)

    return 0.70


def compute_combined_confidence(
    regime_confidence: float,
    forecast_confidence: float,
    signal_confidence: float,
) -> float:
    combined = (
        0.40 * regime_confidence
        + 0.30 * forecast_confidence
        + 0.30 * signal_confidence
    )

    return round(min(max(combined, 0.0), 1.0), 4)


def confidence_to_exposure_multiplier(confidence: float) -> float:
    if confidence >= 0.80:
        return 1.00

    if confidence >= 0.65:
        return 0.85

    if confidence >= 0.50:
        return 0.70

    if confidence >= 0.35:
        return 0.55

    return 0.40


def adjust_portfolio_for_confidence(
    weights: Dict[str, float],
    exposure_multiplier: float,
) -> Dict[str, float]:
    adjusted = {}

    released_weight = 0.0

    for asset, weight in weights.items():
        if asset in RISK_ASSETS:
            new_weight = weight * exposure_multiplier
            released_weight += weight - new_weight
            adjusted[asset] = new_weight
        else:
            adjusted[asset] = weight

    adjusted[CASH_ASSET] = adjusted.get(CASH_ASSET, 0.0) + released_weight

    total = sum(adjusted.values())

    if total <= 0:
        raise ValueError("Adjusted portfolio has non-positive total weight.")

    adjusted = {asset: weight / total for asset, weight in adjusted.items()}

    return adjusted


def build_confidence_adjusted_portfolio() -> tuple[pd.DataFrame, dict]:
    library = load_json(PORTFOLIO_LIBRARY_PATH)
    transition = load_json(TRANSITION_DECISION_PATH)

    effective_regime = transition["effective_allocation_regime"]
    regime_confidence = float(transition.get("regime_confidence", 0.70))

    regime_portfolios = library["regime_portfolios"]

    if effective_regime not in regime_portfolios:
        raise ValueError(f"Effective regime not found in portfolio library: {effective_regime}")

    base_payload = regime_portfolios[effective_regime]
    base_weights = base_payload["weights"]

    forecast_confidence = get_forecast_confidence()
    signal_confidence = get_signal_confidence()

    combined_confidence = compute_combined_confidence(
        regime_confidence=regime_confidence,
        forecast_confidence=forecast_confidence,
        signal_confidence=signal_confidence,
    )

    exposure_multiplier = confidence_to_exposure_multiplier(combined_confidence)

    adjusted_weights = adjust_portfolio_for_confidence(
        weights=base_weights,
        exposure_multiplier=exposure_multiplier,
    )

    records = []
    for asset, weight in adjusted_weights.items():
        records.append(
            {
                "asset": asset,
                "base_weight": round(float(base_weights.get(asset, 0.0)), 6),
                "confidence_adjusted_weight": round(float(weight), 6),
                "weight_delta": round(float(weight - base_weights.get(asset, 0.0)), 6),
                "asset_bucket": (
                    "risk_asset"
                    if asset in RISK_ASSETS
                    else "defensive_asset"
                    if asset in DEFENSIVE_ASSETS
                    else "cash"
                ),
            }
        )

    df = pd.DataFrame(records)

    summary = {
        "module": "confidence_weighted_exposure_engine",
        "effective_regime": effective_regime,
        "selected_portfolio_type": base_payload["portfolio_type"],
        "regime_confidence": round(regime_confidence, 4),
        "forecast_confidence": round(forecast_confidence, 4),
        "signal_confidence": round(signal_confidence, 4),
        "combined_confidence": combined_confidence,
        "exposure_multiplier": exposure_multiplier,
        "risk_assets_scaled": RISK_ASSETS,
        "cash_weight_after_adjustment": round(
            float(df.loc[df["asset"] == CASH_ASSET, "confidence_adjusted_weight"].iloc[0]),
            6,
        ),
        "interpretation": (
            "Risk assets are scaled down when confidence is weak. "
            "Released capital is moved into CASH while defensive assets are preserved."
        ),
    }

    return df, summary


def save_outputs(df: pd.DataFrame, summary: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")


def main() -> None:
    df, summary = build_confidence_adjusted_portfolio()
    save_outputs(df, summary)

    print("=" * 80)
    print("AURUM CONFIDENCE WEIGHTED EXPOSURE ENGINE")
    print("=" * 80)
    print(f"Effective Regime:       {summary['effective_regime']}")
    print(f"Portfolio Type:         {summary['selected_portfolio_type']}")
    print(f"Regime Confidence:      {summary['regime_confidence']}")
    print(f"Forecast Confidence:    {summary['forecast_confidence']}")
    print(f"Signal Confidence:      {summary['signal_confidence']}")
    print(f"Combined Confidence:    {summary['combined_confidence']}")
    print(f"Exposure Multiplier:    {summary['exposure_multiplier']}")
    print()
    print(df.to_string(index=False))
    print()
    print(f"Saved portfolio: {OUTPUT_PATH}")
    print(f"Saved summary:   {SUMMARY_PATH}")


if __name__ == "__main__":
    main()