from __future__ import annotations

from pathlib import Path

from src.institutional.mars_cvar_product import build_reference_product_evidence


ROOT = Path(__file__).resolve().parents[1]
PROJECT = "AURUM - Quantitative Risk and Portfolio Intelligence"
ALGORITHM = "MARS-CVaR"
SUBTITLE = "An institutional quantitative research workstation for regime evidence, tail-risk allocation, and human-gated portfolio governance."
PORT = 8811
THEME = "aurum"
CONTROLS = [
    {"key": "stress_probability", "label": "Next-regime stress probability", "default": 0.50, "min": 0, "max": 1, "step": 0.05},
    {"key": "turnover_penalty", "label": "Turnover penalty tau", "default": 0.05, "min": 0, "max": 0.25, "step": 0.01},
    {"key": "risk_aversion", "label": "CVaR risk weight lambda", "default": 0.35, "min": 0, "max": 3, "step": 0.05},
    {"key": "alpha", "label": "CVaR confidence alpha", "default": 0.95, "min": 0.80, "max": 0.99, "step": 0.01},
]
DEFAULTS = {x["key"]: x["default"] for x in CONTROLS}
DEMO_STRESS = {"stress_probability": 0.75, "turnover_penalty": 0.08, "risk_aversion": 0.35, "alpha": 0.95}


def _merged_params(params: dict) -> dict:
    merged = dict(DEFAULTS)
    merged.update({key: value for key, value in params.items() if key in merged})
    normalized = {key: float(value) for key, value in merged.items()}
    for control in CONTROLS:
        value = normalized[control["key"]]
        if not control["min"] <= value <= control["max"]:
            raise ValueError(f"{control['key']} must be in [{control['min']}, {control['max']}]")
    return normalized


def _display_metrics(raw: dict) -> list[list[str]]:
    return [
        ["Expected return", f"{100 * raw['expected_return']:.3f}% per reference period"],
        ["CVaR signed loss", f"{100 * raw['cvar_loss']:.3f}%"],
        ["Downside loss magnitude", f"{100 * max(0.0, raw['cvar_loss']):.3f}%"],
        ["L1 turnover", f"{100 * raw['turnover']:.2f}%"],
        ["Stress probability", f"{100 * raw['regime_probabilities']['stress']:.0f}%"],
    ]


def compute(params: dict | None = None) -> dict:
    params = _merged_params(params or DEFAULTS)
    evidence = build_reference_product_evidence(ROOT, **params)
    raw = evidence["decision"]
    summary = evidence["walk_forward_research"].get("summary", {})
    actions = [
        {
            "asset": asset,
            "current_weight": f"{100 * evidence['portfolio_workspace']['current_weights'][asset]:.2f}%",
            "target_weight": f"{100 * raw['target_weights'][asset]:.2f}%",
            "change": f"{100 * raw['weight_changes'][asset]:+.2f}%",
        }
        for asset in raw["assets"]
    ]
    baselines = [
        {**item, "expected_return": f"{100 * item['expected_return']:.3f}%", "cvar_loss_signed": f"{100 * item['cvar_loss_signed']:.3f}%", "turnover": f"{100 * item['turnover']:.2f}%"}
        for item in evidence["baselines"]
    ]
    return {
        "gate": raw["risk_gate"],
        "optimization_authorization": raw["risk_gate"],
        "research_promotion": evidence["governance"]["research_promotion"],
        "decision_id": raw["decision_id"],
        "metrics": _display_metrics(raw),
        "actions": actions,
        "baselines": baselines,
        "claim": evidence["claim_boundary"],
        "raw": raw,
        "market_regime": evidence["market_regime"],
        "portfolio_workspace": evidence["portfolio_workspace"],
        "risk_lab": evidence["risk_lab"],
        "constraints": evidence["constraints"],
        "transaction_analysis": evidence["transaction_analysis"],
        "frontier": evidence["frontier"],
        "sensitivity": evidence["sensitivity"],
        "stress_testing": evidence["stress_testing"],
        "walk_forward_research": evidence["walk_forward_research"],
        "governance": evidence["governance"],
        "data_provenance": evidence["data_provenance"],
        "summary": {
            "walk_forward_periods": summary.get("periods", "N/A"),
            "walk_forward_no_lookahead": summary.get("no_lookahead", "N/A"),
            "promotion_state": evidence["governance"]["research_promotion"],
        },
    }
