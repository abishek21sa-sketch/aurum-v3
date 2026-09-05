from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd


RESULTS_DIR = Path("results/research")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

REGISTRY_PATH = RESULTS_DIR / "strategy_registry.json"


SCENARIOS = {
    "equity_crash": {
        "description": "Broad equity market crash.",
        "return_shock": -0.18,
        "vol_multiplier": 2.4,
        "drawdown_multiplier": 2.2,
        "liquidity_penalty": 0.04,
    },
    "inflation_shock": {
        "description": "Rates and inflation shock.",
        "return_shock": -0.08,
        "vol_multiplier": 1.7,
        "drawdown_multiplier": 1.5,
        "liquidity_penalty": 0.02,
    },
    "liquidity_crisis": {
        "description": "Market-wide liquidity breakdown.",
        "return_shock": -0.12,
        "vol_multiplier": 2.1,
        "drawdown_multiplier": 2.0,
        "liquidity_penalty": 0.06,
    },
    "crypto_crash": {
        "description": "Severe crypto-led risk-off event.",
        "return_shock": -0.10,
        "vol_multiplier": 1.9,
        "drawdown_multiplier": 1.8,
        "liquidity_penalty": 0.03,
    },
    "risk_on_rally": {
        "description": "High-beta upside rally.",
        "return_shock": 0.09,
        "vol_multiplier": 0.8,
        "drawdown_multiplier": 0.7,
        "liquidity_penalty": 0.00,
    },
}


BASE_STRATEGY_METRICS = {
    "rolling_min_variance": {
        "annual_return": 0.2952,
        "annual_volatility": 0.0794,
        "sharpe": 2.4996,
        "max_drawdown": -0.0464,
        "turnover": 0.4738,
    },
    "risk_parity": {
        "annual_return": 0.2250,
        "annual_volatility": 0.0850,
        "sharpe": 2.0500,
        "max_drawdown": -0.0600,
        "turnover": 0.3500,
    },
    "cvar_optimized": {
        "annual_return": 0.2050,
        "annual_volatility": 0.0760,
        "sharpe": 1.9500,
        "max_drawdown": -0.0520,
        "turnover": 0.3000,
    },
    "regime_aware": {
        "annual_return": 0.2161,
        "annual_volatility": 0.0580,
        "sharpe": 2.0577,
        "max_drawdown": -0.0313,
        "turnover": 0.4200,
    },
    "black_litterman": {
        "annual_return": 0.3351,
        "annual_volatility": 0.1903,
        "sharpe": 1.3215,
        "max_drawdown": -0.0990,
        "turnover": 0.0505,
    },
    "bayesian_robust": {
        "annual_return": 0.1736,
        "annual_volatility": 0.1364,
        "sharpe": 1.0163,
        "max_drawdown": -0.1384,
        "turnover": 0.1444,
    },
    "meta_strategy": {
        "annual_return": 0.2023,
        "annual_volatility": 0.0634,
        "sharpe": 2.5213,
        "max_drawdown": -0.0329,
        "turnover": 0.2500,
    },
}


STRATEGY_SENSITIVITY = {
    "rolling_min_variance": 0.55,
    "risk_parity": 0.70,
    "cvar_optimized": 0.45,
    "regime_aware": 0.50,
    "black_litterman": 0.95,
    "bayesian_robust": 0.65,
    "meta_strategy": 0.42,
}


def load_registry() -> Dict[str, dict]:
    if not REGISTRY_PATH.exists():
        from src.research.strategy_registry import build_strategy_registry

        build_strategy_registry()

    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def stress_test_strategies() -> Path:
    registry = load_registry()
    rows: List[dict] = []

    for strategy_id, profile in registry.items():
        base = BASE_STRATEGY_METRICS.get(strategy_id)
        if base is None:
            continue

        sensitivity = STRATEGY_SENSITIVITY.get(strategy_id, 0.75)

        for scenario_id, scenario in SCENARIOS.items():
            shocked_return = base["annual_return"] + scenario["return_shock"] * sensitivity
            shocked_vol = base["annual_volatility"] * scenario["vol_multiplier"] * sensitivity
            shocked_drawdown = base["max_drawdown"] * scenario["drawdown_multiplier"] * sensitivity
            liquidity_cost = scenario["liquidity_penalty"] * sensitivity
            stressed_sharpe = shocked_return / shocked_vol if shocked_vol > 0 else 0.0

            rows.append(
                {
                    "strategy_id": strategy_id,
                    "strategy_name": profile["name"],
                    "category": profile["category"],
                    "scenario_id": scenario_id,
                    "scenario_description": scenario["description"],
                    "base_return": base["annual_return"],
                    "base_volatility": base["annual_volatility"],
                    "base_sharpe": base["sharpe"],
                    "base_max_drawdown": base["max_drawdown"],
                    "base_turnover": base["turnover"],
                    "stressed_return": shocked_return,
                    "stressed_volatility": shocked_vol,
                    "stressed_sharpe": stressed_sharpe,
                    "stressed_max_drawdown": shocked_drawdown,
                    "liquidity_cost": liquidity_cost,
                    "stress_loss": base["annual_return"] - shocked_return,
                }
            )

    df = pd.DataFrame(rows)
    output_path = RESULTS_DIR / "strategy_stress_results.csv"
    df.to_csv(output_path, index=False)

    return output_path


if __name__ == "__main__":
    path = stress_test_strategies()
    print("=" * 80)
    print("AURUM STRATEGY STRESS TESTER")
    print("=" * 80)
    print(f"Saved: {path}")