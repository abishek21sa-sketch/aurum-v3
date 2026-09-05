from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


INPUT_DIR = Path("results/regime_intelligence")
OUTPUT_DIR = Path("results/regime_intelligence")

CONFIDENCE_PORTFOLIO_PATH = INPUT_DIR / "confidence_adjusted_portfolio.csv"
HEDGE_OVERLAY_PATH = INPUT_DIR / "dynamic_hedge_overlay.json"
TRANSITION_DECISION_PATH = INPUT_DIR / "transition_decision.json"

OUTPUT_PATH = OUTPUT_DIR / "final_regime_allocation.csv"
SUMMARY_PATH = OUTPUT_DIR / "final_regime_allocation_summary.json"


RISK_ASSETS = ["SPY", "QQQ", "DIA", "BTC-USD", "ETH-USD"]
DEFENSIVE_ASSETS = ["TLT", "GLD", "VIX", "CASH"]


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_confidence_portfolio() -> pd.DataFrame:
    if not CONFIDENCE_PORTFOLIO_PATH.exists():
        raise FileNotFoundError(f"Missing required input: {CONFIDENCE_PORTFOLIO_PATH}")

    df = pd.read_csv(CONFIDENCE_PORTFOLIO_PATH)

    required = {"asset", "confidence_adjusted_weight"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Confidence portfolio missing columns: {missing}")

    return df


def apply_hedge_overlay(base_df: pd.DataFrame, overlay: dict) -> pd.DataFrame:
    base = {
        row["asset"]: float(row["confidence_adjusted_weight"])
        for _, row in base_df.iterrows()
    }

    overlay_weights = overlay["overlay_weights"]
    total_overlay = float(overlay["total_overlay_weight"])

    if total_overlay <= 0:
        final = base.copy()
    else:
        risk_weight_total = sum(base.get(asset, 0.0) for asset in RISK_ASSETS)

        final = base.copy()

        if risk_weight_total > 0:
            for asset in RISK_ASSETS:
                current_weight = final.get(asset, 0.0)
                funding_cut = total_overlay * (current_weight / risk_weight_total)
                final[asset] = max(current_weight - funding_cut, 0.0)
        else:
            cash_weight = final.get("CASH", 0.0)
            final["CASH"] = max(cash_weight - total_overlay, 0.0)

        for asset, hedge_weight in overlay_weights.items():
            final[asset] = final.get(asset, 0.0) + float(hedge_weight)

    total = sum(final.values())

    if total <= 0:
        raise ValueError("Final allocation has non-positive total weight.")

    final = {asset: weight / total for asset, weight in final.items()}

    records = []

    for asset in sorted(final.keys()):
        base_weight = base.get(asset, 0.0)
        final_weight = final[asset]

        records.append(
            {
                "asset": asset,
                "base_confidence_weight": round(base_weight, 6),
                "final_weight": round(final_weight, 6),
                "final_weight_pct": round(final_weight * 100, 2),
                "overlay_delta": round(final_weight - base_weight, 6),
                "asset_bucket": (
                    "risk_asset"
                    if asset in RISK_ASSETS
                    else "defensive_or_cash"
                ),
            }
        )

    return pd.DataFrame(records)


def build_final_regime_allocation() -> tuple[pd.DataFrame, dict]:
    base_df = load_confidence_portfolio()
    overlay = load_json(HEDGE_OVERLAY_PATH)
    transition = load_json(TRANSITION_DECISION_PATH)

    final_df = apply_hedge_overlay(base_df, overlay)

    risk_weight = final_df.loc[
        final_df["asset"].isin(RISK_ASSETS),
        "final_weight",
    ].sum()

    defensive_weight = final_df.loc[
        final_df["asset"].isin(DEFENSIVE_ASSETS),
        "final_weight",
    ].sum()

    summary = {
        "module": "regime_allocation_switch_engine",
        "purpose": "Combine regime template, transition decision, confidence scaling, and hedge overlay into one final allocation.",
        "previous_regime": transition["previous_regime"],
        "detected_current_regime": transition["detected_current_regime"],
        "effective_allocation_regime": transition["effective_allocation_regime"],
        "transition_risk_label": transition["transition_risk_label"],
        "transition_risk_score": transition["transition_risk_score"],
        "hedge_status": overlay["hedge_status"],
        "total_overlay_weight": overlay["total_overlay_weight"],
        "final_risk_asset_weight": round(float(risk_weight), 6),
        "final_defensive_or_cash_weight": round(float(defensive_weight), 6),
        "final_allocation_sum": round(float(final_df["final_weight"].sum()), 6),
        "interpretation": (
            "The final allocation starts from the regime portfolio, applies confidence-based exposure scaling, "
            "then funds the hedge overlay by reducing risky assets proportionally."
        ),
    }

    return final_df, summary


def save_outputs(final_df: pd.DataFrame, summary: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(OUTPUT_PATH, index=False)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=4), encoding="utf-8")


def main() -> None:
    final_df, summary = build_final_regime_allocation()
    save_outputs(final_df, summary)

    print("=" * 80)
    print("AURUM REGIME ALLOCATION SWITCH ENGINE")
    print("=" * 80)
    print(f"Previous Regime:       {summary['previous_regime']}")
    print(f"Detected Regime:       {summary['detected_current_regime']}")
    print(f"Effective Regime:      {summary['effective_allocation_regime']}")
    print(f"Transition Risk:       {summary['transition_risk_label']} ({summary['transition_risk_score']})")
    print(f"Hedge Status:          {summary['hedge_status']}")
    print(f"Overlay Weight:        {summary['total_overlay_weight']}")
    print(f"Risk Asset Weight:     {summary['final_risk_asset_weight']}")
    print(f"Defensive/Cash Weight: {summary['final_defensive_or_cash_weight']}")
    print()
    print(final_df.to_string(index=False))
    print()
    print(f"Saved allocation: {OUTPUT_PATH}")
    print(f"Saved summary:    {SUMMARY_PATH}")


if __name__ == "__main__":
    main()