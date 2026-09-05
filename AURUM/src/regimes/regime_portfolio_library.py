from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


OUTPUT_DIR = Path("results/regime_intelligence")
OUTPUT_PATH = OUTPUT_DIR / "regime_portfolio_library.json"


ASSETS = ["SPY", "QQQ", "DIA", "TLT", "GLD", "VIX", "BTC-USD", "ETH-USD", "CASH"]


def validate_portfolio(name: str, weights: Dict[str, float]) -> None:
    missing_assets = set(ASSETS) - set(weights.keys())
    extra_assets = set(weights.keys()) - set(ASSETS)

    if missing_assets:
        raise ValueError(f"{name} portfolio is missing assets: {missing_assets}")

    if extra_assets:
        raise ValueError(f"{name} portfolio has unknown assets: {extra_assets}")

    total_weight = round(sum(weights.values()), 6)
    if total_weight != 1.0:
        raise ValueError(f"{name} portfolio weights sum to {total_weight}, not 1.0")

    for asset, weight in weights.items():
        if weight < 0:
            raise ValueError(f"{name} portfolio has negative weight for {asset}: {weight}")


def build_regime_portfolio_library() -> dict:
    library = {
        "bull": {
            "description": "Growth-oriented allocation for strong risk-on markets.",
            "portfolio_type": "growth_overweight",
            "weights": {
                "SPY": 0.24,
                "QQQ": 0.30,
                "DIA": 0.12,
                "TLT": 0.04,
                "GLD": 0.04,
                "VIX": 0.02,
                "BTC-USD": 0.12,
                "ETH-USD": 0.07,
                "CASH": 0.05,
            },
        },
        "normal": {
            "description": "Balanced multi-asset allocation for stable market conditions.",
            "portfolio_type": "balanced_risk_parity_style",
            "weights": {
                "SPY": 0.20,
                "QQQ": 0.18,
                "DIA": 0.14,
                "TLT": 0.16,
                "GLD": 0.12,
                "VIX": 0.03,
                "BTC-USD": 0.07,
                "ETH-USD": 0.04,
                "CASH": 0.06,
            },
        },
        "high_volatility": {
            "description": "Defensive allocation for unstable but non-crisis markets.",
            "portfolio_type": "volatility_defensive",
            "weights": {
                "SPY": 0.14,
                "QQQ": 0.10,
                "DIA": 0.10,
                "TLT": 0.22,
                "GLD": 0.16,
                "VIX": 0.08,
                "BTC-USD": 0.04,
                "ETH-USD": 0.02,
                "CASH": 0.14,
            },
        },
        "risk_off": {
            "description": "Capital preservation allocation for deteriorating markets.",
            "portfolio_type": "defensive_allocation",
            "weights": {
                "SPY": 0.10,
                "QQQ": 0.06,
                "DIA": 0.08,
                "TLT": 0.28,
                "GLD": 0.18,
                "VIX": 0.08,
                "BTC-USD": 0.02,
                "ETH-USD": 0.01,
                "CASH": 0.19,
            },
        },
        "liquidity_stress": {
            "description": "Liquidity-preserving allocation with elevated cash and safe-haven exposure.",
            "portfolio_type": "liquidity_defense",
            "weights": {
                "SPY": 0.08,
                "QQQ": 0.04,
                "DIA": 0.06,
                "TLT": 0.24,
                "GLD": 0.18,
                "VIX": 0.08,
                "BTC-USD": 0.01,
                "ETH-USD": 0.01,
                "CASH": 0.30,
            },
        },
        "crisis": {
            "description": "Maximum defense allocation for systemic crisis conditions.",
            "portfolio_type": "crisis_capital_preservation",
            "weights": {
                "SPY": 0.04,
                "QQQ": 0.02,
                "DIA": 0.04,
                "TLT": 0.30,
                "GLD": 0.22,
                "VIX": 0.12,
                "BTC-USD": 0.00,
                "ETH-USD": 0.00,
                "CASH": 0.26,
            },
        },
    }

    for regime_name, payload in library.items():
        validate_portfolio(regime_name, payload["weights"])

    return {
        "module": "regime_portfolio_library",
        "purpose": "Institutional regime-specific portfolio templates for AURUM Chat 3C.",
        "assets": ASSETS,
        "regime_portfolios": library,
    }


def save_library(library: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(library, indent=4), encoding="utf-8")


def main() -> None:
    library = build_regime_portfolio_library()
    save_library(library)

    print("=" * 80)
    print("AURUM REGIME PORTFOLIO LIBRARY")
    print("=" * 80)
    print(f"Saved: {OUTPUT_PATH}")
    print()
    for regime, payload in library["regime_portfolios"].items():
        print(f"{regime:20s} | {payload['portfolio_type']}")


if __name__ == "__main__":
    main()