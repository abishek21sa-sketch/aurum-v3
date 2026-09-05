from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


OUTPUT_DIR = Path("results/portfolio_lab")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_PORTFOLIO_PATH = Path("results/portfolio/realtime_optimized_portfolio.json")
FALLBACK_PORTFOLIO_PATH = Path("results/execution/current_portfolio_state.json")

LAB_REPORT_JSON = OUTPUT_DIR / "portfolio_lab_report.json"
LAB_COMPARISON_CSV = OUTPUT_DIR / "portfolio_lab_comparison.csv"
LAB_REPORT_TXT = OUTPUT_DIR / "portfolio_lab_report.txt"


DEFAULT_CURRENT_WEIGHTS = {
    "SPY": 0.25,
    "QQQ": 0.22,
    "DIA": 0.10,
    "TLT": 0.15,
    "GLD": 0.10,
    "BTC-USD": 0.05,
    "ETH-USD": 0.03,
    "CASH": 0.10,
}


DEFAULT_RISK_ASSUMPTIONS = {
    "SPY": {"return": 0.085, "vol": 0.16},
    "QQQ": {"return": 0.110, "vol": 0.22},
    "DIA": {"return": 0.075, "vol": 0.15},
    "TLT": {"return": 0.045, "vol": 0.13},
    "GLD": {"return": 0.055, "vol": 0.14},
    "BTC-USD": {"return": 0.180, "vol": 0.65},
    "ETH-USD": {"return": 0.200, "vol": 0.75},
    "CASH": {"return": 0.035, "vol": 0.01},
}


SCENARIOS = {
    "current": {},
    "cash_20": {"CASH": 0.20},
    "gld_15": {"GLD": 0.15},
    "cut_qqq_10": {"QQQ": -0.10},
    "defensive_rotation": {
        "SPY": -0.05,
        "QQQ": -0.07,
        "DIA": -0.03,
        "TLT": 0.06,
        "GLD": 0.05,
        "CASH": 0.04,
    },
    "risk_on_rotation": {
        "SPY": 0.04,
        "QQQ": 0.06,
        "DIA": 0.02,
        "TLT": -0.04,
        "GLD": -0.03,
        "CASH": -0.05,
    },
}


@dataclass
class PortfolioMetrics:
    expected_return: float
    volatility: float
    sharpe: float
    cvar_proxy: float
    max_drawdown_proxy: float
    concentration: float
    cash_weight: float


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    clean = {k: max(float(v), 0.0) for k, v in weights.items()}
    total = sum(clean.values())

    if total <= 0:
        return DEFAULT_CURRENT_WEIGHTS.copy()

    return {k: v / total for k, v in clean.items()}


def extract_weights_from_payload(payload: Dict[str, Any]) -> Dict[str, float]:
    if not payload:
        return DEFAULT_CURRENT_WEIGHTS.copy()

    for key in ["weights", "portfolio_weights", "target_weights", "current_weights"]:
        candidate = payload.get(key)
        if isinstance(candidate, dict) and candidate:
            return normalize_weights({str(k): float(v) for k, v in candidate.items()})

    holdings = payload.get("holdings") or payload.get("positions")

    if isinstance(holdings, list):
        weights = {}

        for row in holdings:
            if not isinstance(row, dict):
                continue

            ticker = row.get("ticker") or row.get("asset") or row.get("symbol")
            weight = row.get("weight") or row.get("target_weight") or row.get("current_weight")

            if ticker is not None and weight is not None:
                weights[str(ticker)] = float(weight)

        if weights:
            return normalize_weights(weights)

    return DEFAULT_CURRENT_WEIGHTS.copy()


def load_current_portfolio() -> Dict[str, float]:
    payload = load_json(CURRENT_PORTFOLIO_PATH)

    if payload:
        return extract_weights_from_payload(payload)

    payload = load_json(FALLBACK_PORTFOLIO_PATH)

    if payload:
        return extract_weights_from_payload(payload)

    return DEFAULT_CURRENT_WEIGHTS.copy()


def apply_scenario(
    base_weights: Dict[str, float],
    scenario_changes: Dict[str, float],
) -> Dict[str, float]:
    weights = base_weights.copy()

    absolute_keys = {"CASH", "GLD"}

    for asset, change in scenario_changes.items():
        if asset in absolute_keys and change >= 0.15:
            weights[asset] = change
        else:
            weights[asset] = weights.get(asset, 0.0) + change

    return normalize_weights(weights)


def calculate_metrics(weights: Dict[str, float]) -> PortfolioMetrics:
    expected_return = 0.0
    variance_proxy = 0.0

    for asset, weight in weights.items():
        assumptions = DEFAULT_RISK_ASSUMPTIONS.get(
            asset,
            {"return": 0.06, "vol": 0.20},
        )

        expected_return += weight * assumptions["return"]
        variance_proxy += (weight * assumptions["vol"]) ** 2

    volatility = variance_proxy ** 0.5
    sharpe = expected_return / volatility if volatility > 0 else 0.0
    cvar_proxy = volatility * 2.15
    max_drawdown_proxy = volatility * 2.75
    concentration = sum(w ** 2 for w in weights.values())
    cash_weight = weights.get("CASH", 0.0)

    return PortfolioMetrics(
        expected_return=expected_return,
        volatility=volatility,
        sharpe=sharpe,
        cvar_proxy=cvar_proxy,
        max_drawdown_proxy=max_drawdown_proxy,
        concentration=concentration,
        cash_weight=cash_weight,
    )


def compare_to_current(
    current_metrics: PortfolioMetrics,
    scenario_metrics: PortfolioMetrics,
) -> Dict[str, float]:
    return {
        "expected_return_change": scenario_metrics.expected_return
        - current_metrics.expected_return,
        "volatility_change": scenario_metrics.volatility
        - current_metrics.volatility,
        "sharpe_change": scenario_metrics.sharpe - current_metrics.sharpe,
        "cvar_proxy_change": scenario_metrics.cvar_proxy
        - current_metrics.cvar_proxy,
        "max_drawdown_proxy_change": scenario_metrics.max_drawdown_proxy
        - current_metrics.max_drawdown_proxy,
        "concentration_change": scenario_metrics.concentration
        - current_metrics.concentration,
        "cash_weight_change": scenario_metrics.cash_weight
        - current_metrics.cash_weight,
    }


def run_portfolio_lab() -> Dict[str, Any]:
    current_weights = load_current_portfolio()
    current_metrics = calculate_metrics(current_weights)

    rows: List[Dict[str, Any]] = []
    scenario_payloads: Dict[str, Any] = {}

    for scenario_name, changes in SCENARIOS.items():
        if scenario_name == "current":
            scenario_weights = current_weights
        else:
            scenario_weights = apply_scenario(current_weights, changes)

        scenario_metrics = calculate_metrics(scenario_weights)
        delta = compare_to_current(current_metrics, scenario_metrics)

        row = {
            "scenario": scenario_name,
            **asdict(scenario_metrics),
            **delta,
        }

        rows.append(row)

        scenario_payloads[scenario_name] = {
            "weights": scenario_weights,
            "metrics": asdict(scenario_metrics),
            "delta_vs_current": delta,
        }

    comparison = pd.DataFrame(rows)
    comparison.to_csv(LAB_COMPARISON_CSV, index=False)

    best_sharpe = comparison.sort_values("sharpe", ascending=False).iloc[0]
    lowest_vol = comparison.sort_values("volatility", ascending=True).iloc[0]
    lowest_drawdown = comparison.sort_values("max_drawdown_proxy", ascending=True).iloc[0]

    report = {
        "platform": "AURUM",
        "phase": "Phase 4I",
        "module": "Portfolio Laboratory",
        "status": "complete",
        "current_portfolio": {
            "weights": current_weights,
            "metrics": asdict(current_metrics),
        },
        "scenario_count": len(SCENARIOS),
        "scenarios": scenario_payloads,
        "summary": {
            "best_sharpe_scenario": str(best_sharpe["scenario"]),
            "lowest_volatility_scenario": str(lowest_vol["scenario"]),
            "lowest_drawdown_scenario": str(lowest_drawdown["scenario"]),
        },
    }

    LAB_REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM PORTFOLIO LABORATORY REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Scenario Count: {len(SCENARIOS)}")
    lines.append(f"Best Sharpe Scenario: {report['summary']['best_sharpe_scenario']}")
    lines.append(f"Lowest Volatility Scenario: {report['summary']['lowest_volatility_scenario']}")
    lines.append(f"Lowest Drawdown Scenario: {report['summary']['lowest_drawdown_scenario']}")
    lines.append("")
    lines.append("SCENARIO COMPARISON")
    lines.append("-" * 80)

    for _, row in comparison.iterrows():
        lines.append(
            f"{row['scenario']} | "
            f"return={row['expected_return']:.4f} | "
            f"vol={row['volatility']:.4f} | "
            f"sharpe={row['sharpe']:.4f} | "
            f"cvar={row['cvar_proxy']:.4f} | "
            f"drawdown={row['max_drawdown_proxy']:.4f} | "
            f"cash={row['cash_weight']:.4f}"
        )

    LAB_REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")

    return report


if __name__ == "__main__":
    result = run_portfolio_lab()

    print("=" * 80)
    print("AURUM PORTFOLIO LABORATORY")
    print("=" * 80)
    print(f"Status: {result['status']}")
    print(f"Scenario Count: {result['scenario_count']}")
    print(f"Best Sharpe Scenario: {result['summary']['best_sharpe_scenario']}")
    print(f"Lowest Volatility Scenario: {result['summary']['lowest_volatility_scenario']}")
    print(f"Lowest Drawdown Scenario: {result['summary']['lowest_drawdown_scenario']}")
    print(f"Saved: {LAB_REPORT_JSON}")
    print(f"Saved: {LAB_COMPARISON_CSV}")
    print(f"Saved: {LAB_REPORT_TXT}")