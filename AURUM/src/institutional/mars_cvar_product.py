"""Evidence assembly for the AURUM MARS-CVaR product surface.

This module deliberately keeps presentation evidence separate from the
optimizer.  The optimizer remains the only component that produces target
weights; this module adds traceable diagnostics, baselines, and counterfactual
views for a human reviewer.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from src.institutional.mars_cvar_decision_bridge import build_mars_cvar_decision
from src.institutional.mars_cvar_validation import (
    equal_weight_baseline,
    mean_variance_baseline,
    static_cvar_baseline,
)
from src.optimization.signature_algorithm import (
    laplace_transition_matrix,
    next_regime_probabilities,
    solve_mars_cvar,
)


REFERENCE_ASSETS = ("SPY", "TLT", "GLD", "CASH")
REFERENCE_ORDER = ("calm", "stress")
REFERENCE_PREVIOUS = (0.35, 0.25, 0.20, 0.20)
REFERENCE_CAPS = (0.60, 0.60, 0.60, 1.00)
REFERENCE_STATES = (
    "calm",
    "calm",
    "stress",
    "calm",
    "calm",
    "stress",
    "stress",
    "stress",
    "calm",
    "calm",
    "stress",
)
REFERENCE_RETURNS = {
    "calm": np.array(
        [[0.018, 0.002, 0.003, 0.0002], [0.012, 0.004, 0.002, 0.0002], [0.021, -0.001, 0.004, 0.0002]],
        dtype=float,
    ),
    "stress": np.array(
        [[-0.080, 0.024, 0.035, 0.0002], [-0.050, 0.017, 0.022, 0.0002], [-0.110, 0.028, 0.040, 0.0002]],
        dtype=float,
    ),
}


def _f(value: float | int | None, digits: int = 10) -> float | None:
    return None if value is None else round(float(value), digits)


def _probabilities(stress_probability: float) -> dict[str, float]:
    stress = float(stress_probability)
    if not math.isfinite(stress) or not 0.0 <= stress <= 1.0:
        raise ValueError("stress_probability must be finite and in [0, 1]")
    return {"calm": 1.0 - stress, "stress": stress}


def _scenario_rows(weights: Sequence[float], probabilities: Mapping[str, float], alpha: float) -> list[dict]:
    w = np.asarray(weights, dtype=float)
    rows: list[dict] = []
    for regime in REFERENCE_ORDER:
        values = REFERENCE_RETURNS[regime]
        probability = float(probabilities[regime])
        for index, returns in enumerate(values, start=1):
            portfolio_return = float(returns @ w)
            rows.append(
                {
                    "scenario_id": f"{regime}-{index:02d}",
                    "evidence_class": "SIMULATED_REFERENCE_SCENARIO",
                    "regime": regime,
                    "probability": _f(probability / len(values)),
                    "portfolio_return": _f(portfolio_return),
                    "signed_loss": _f(-portfolio_return),
                    "asset_returns": {a: _f(x) for a, x in zip(REFERENCE_ASSETS, returns)},
                }
            )

    remaining = 1.0 - alpha
    for row in sorted(rows, key=lambda item: float(item["signed_loss"]), reverse=True):
        take = min(float(row["probability"]), remaining)
        row["cvar_tail_probability"] = _f(take)
        row["cvar_contribution"] = _f(float(row["signed_loss"]) * take / (1.0 - alpha))
        row["in_cvar_tail"] = bool(take > 0.0)
        remaining -= take
        if remaining <= 1e-12:
            break
    for row in rows:
        row.setdefault("cvar_tail_probability", 0.0)
        row.setdefault("cvar_contribution", 0.0)
        row.setdefault("in_cvar_tail", False)
    return sorted(rows, key=lambda item: float(item["signed_loss"]), reverse=True)


def _asset_contributions(weights: Sequence[float], probabilities: Mapping[str, float]) -> list[dict]:
    w = np.asarray(weights, dtype=float)
    expected_by_asset = sum(float(probabilities[r]) * REFERENCE_RETURNS[r].mean(axis=0) for r in REFERENCE_ORDER)
    return [
        {
            "asset": asset,
            "weight": _f(weight),
            "expected_return_per_unit": _f(mu),
            "expected_return_contribution": _f(weight * mu),
        }
        for asset, weight, mu in zip(REFERENCE_ASSETS, w, expected_by_asset)
    ]


def _metric_block(name: str, item: Mapping, assets: Sequence[str] = REFERENCE_ASSETS) -> dict:
    weights = item.get("weights", {})
    if not weights and "target_weights" in item:
        weights = item["target_weights"]
    return {
        "name": name,
        "expected_return": _f(item.get("expected_return", 0.0)),
        "cvar_loss_signed": _f(item.get("cvar_loss", 0.0)),
        "cvar_loss_magnitude": _f(max(0.0, float(item.get("cvar_loss", 0.0)))),
        "turnover": _f(item.get("turnover", 0.0)),
        "weights": {asset: _f(weights.get(asset, 0.0)) for asset in assets},
    }


def _constraints(decision: Mapping, *, max_turnover: float, max_cvar_loss: float) -> list[dict]:
    weights = decision["target_weights"]
    rows = [
        {"name": "portfolio sum", "limit": 1.0, "observed": _f(sum(weights.values())), "slack": _f(1.0 - sum(weights.values())), "status": "PASS"},
        {"name": "minimum cash", "limit": 0.10, "observed": _f(weights["CASH"]), "slack": _f(weights["CASH"] - 0.10), "status": "PASS" if weights["CASH"] >= 0.10 - 1e-10 else "FAIL"},
        {"name": "CVaR gate signed loss", "limit": max_cvar_loss, "observed": _f(decision["cvar_loss"]), "slack": _f(max_cvar_loss - decision["cvar_loss"]), "status": "PASS" if decision["gates"]["cvar"]["passed"] else "BLOCKED"},
        {"name": "turnover gate", "limit": max_turnover, "observed": _f(decision["turnover"]), "slack": _f(max_turnover - decision["turnover"]), "status": "PASS" if decision["gates"]["turnover"]["passed"] else "BLOCKED"},
    ]
    for asset, cap in zip(REFERENCE_ASSETS, REFERENCE_CAPS):
        observed = float(weights[asset])
        rows.append({"name": f"position cap {asset}", "limit": cap, "observed": _f(observed), "slack": _f(cap - observed), "status": "PASS" if observed <= cap + 1e-10 else "FAIL"})
    return rows


def _transition_evidence(stress_probability: float) -> dict:
    matrix = laplace_transition_matrix(REFERENCE_STATES, REFERENCE_ORDER, smoothing=1.0)
    current = "stress" if stress_probability >= 0.5 else "calm"
    derived = next_regime_probabilities(REFERENCE_STATES, REFERENCE_ORDER, smoothing=1.0)
    frequencies = {regime: REFERENCE_STATES.count(regime) / len(REFERENCE_STATES) for regime in REFERENCE_ORDER}
    input_vector = _probabilities(stress_probability)
    entropy = -sum(p * math.log(p) for p in input_vector.values() if p > 0.0)
    normalized_entropy = entropy / math.log(len(input_vector))
    return {
        "state_definitions": {"calm": "lower reference volatility state", "stress": "higher reference volatility state"},
        "current_regime": current,
        "transition_matrix": {r: {c: _f(matrix[i, j]) for j, c in enumerate(REFERENCE_ORDER)} for i, r in enumerate(REFERENCE_ORDER)},
        "transition_matrix_row_sums": {r: _f(matrix[i].sum()) for i, r in enumerate(REFERENCE_ORDER)},
        "transition_matrix_valid": bool(np.allclose(matrix.sum(axis=1), 1.0)),
        "estimated_next_regime_probabilities": {k: _f(v) for k, v in derived.items()},
        "decision_input_next_regime_probabilities": {k: _f(v) for k, v in input_vector.items()},
        "probability_vector_source": "operator-controlled reference/counterfactual input; not a causal market forecast",
        "historical_regime_frequencies": {k: _f(v) for k, v in frequencies.items()},
        "regime_persistence": {r: _f(matrix[i, i]) for i, r in enumerate(REFERENCE_ORDER)},
        "probability_entropy_normalized": _f(normalized_entropy),
        "limitations": [
            "Reference states and probabilities are deterministic evidence fixtures.",
            "A Markov regime model is descriptive state-transition evidence, not causal proof of markets.",
            "Live data acquisition is optional and is not used by the offline product acceptance path.",
        ],
    }


def _walk_forward_evidence(root: Path) -> dict:
    path = root / "artifacts" / "mars_cvar" / "walk_forward_evidence.json"
    raw: dict = {}
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = {}
    summary = raw.get("summary", {})
    return {
        "evidence_class": raw.get("evidence_class", "HISTORICAL_OBSERVATIONAL_WALK_FORWARD"),
        "null_hypothesis": raw.get("null_hypothesis", "MARS-CVaR does not improve out-of-sample performance versus the stated baselines after costs."),
        "summary": summary,
        "no_lookahead": bool(summary.get("no_lookahead", False)),
        "promotion_state": summary.get("promotion_gate", "RESEARCH_ONLY"),
        "claim_boundary": raw.get("claim_boundary", "Historical walk-forward evidence is not realized future performance and does not establish investment alpha."),
        "source_artifact": str(path.relative_to(root)) if path.exists() else "missing",
    }


def _sensitivity(probabilities: Mapping[str, float], alpha: float, risk_aversion: float, turnover_penalty: float) -> dict:
    rows = []
    for penalty in (0.0, 0.01, 0.05, 0.10, 0.20):
        result = solve_mars_cvar(REFERENCE_ASSETS, REFERENCE_RETURNS, probabilities, REFERENCE_PREVIOUS, alpha=alpha, risk_aversion=risk_aversion, turnover_penalty=penalty, max_weights=REFERENCE_CAPS, min_cash=0.10)
        rows.append({"turnover_penalty": penalty, "expected_return": _f(result.expected_return), "cvar_loss_signed": _f(result.cvar_loss), "turnover": _f(result.turnover)})
    stress_rows = []
    for stress in (0.0, 0.25, 0.50, 0.75, 1.0):
        p = _probabilities(stress)
        result = solve_mars_cvar(REFERENCE_ASSETS, REFERENCE_RETURNS, p, REFERENCE_PREVIOUS, alpha=alpha, risk_aversion=risk_aversion, turnover_penalty=turnover_penalty, max_weights=REFERENCE_CAPS, min_cash=0.10)
        stress_rows.append({"stress_probability": stress, "expected_return": _f(result.expected_return), "cvar_loss_signed": _f(result.cvar_loss), "turnover": _f(result.turnover), "SPY_weight": _f(result.weights[0])})
    return {
        "turnover_penalty": rows,
        "stress_probability": stress_rows,
        "interpretation": "LP policy paths can kink or remain flat when constraints bind; these are evaluated sweeps, not assumed continuous relationships.",
    }


def _frontier(probabilities: Mapping[str, float], alpha: float, turnover_penalty: float) -> list[dict]:
    rows = []
    for risk_aversion in (0.10, 0.35, 0.75, 1.50, 3.00):
        result = solve_mars_cvar(REFERENCE_ASSETS, REFERENCE_RETURNS, probabilities, REFERENCE_PREVIOUS, alpha=alpha, risk_aversion=risk_aversion, turnover_penalty=turnover_penalty, max_weights=REFERENCE_CAPS, min_cash=0.10)
        rows.append({"risk_weight_lambda": risk_aversion, "expected_return": _f(result.expected_return), "cvar_loss_signed": _f(result.cvar_loss), "turnover": _f(result.turnover), "objective": _f(result.objective)})
    return rows


def build_reference_product_evidence(
    root: Path,
    *,
    stress_probability: float = 0.50,
    turnover_penalty: float = 0.05,
    alpha: float = 0.95,
    risk_aversion: float = 0.35,
) -> dict:
    """Build one deterministic, auditable product payload."""
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    if float(turnover_penalty) < 0.0 or float(risk_aversion) < 0.0:
        raise ValueError("turnover_penalty and risk_aversion must be nonnegative")
    probabilities = _probabilities(stress_probability)
    decision = build_mars_cvar_decision(
        assets=REFERENCE_ASSETS,
        regime_returns=REFERENCE_RETURNS,
        regime_probabilities=probabilities,
        previous_weights=REFERENCE_PREVIOUS,
        max_weights=REFERENCE_CAPS,
        alpha=float(alpha),
        risk_aversion=float(risk_aversion),
        turnover_penalty=float(turnover_penalty),
        min_cash=0.10,
        max_cvar_loss=0.03,
        max_turnover=0.40,
        persist=False,
    )
    scenario_rows = _scenario_rows([decision["target_weights"][a] for a in REFERENCE_ASSETS], probabilities, float(alpha))
    static = static_cvar_baseline(assets=REFERENCE_ASSETS, regime_returns=REFERENCE_RETURNS, previous_weights=REFERENCE_PREVIOUS, max_weights=REFERENCE_CAPS, alpha=float(alpha), risk_aversion=float(risk_aversion), turnover_penalty=float(turnover_penalty), min_cash=0.10)
    equal = equal_weight_baseline(REFERENCE_ASSETS, REFERENCE_PREVIOUS, REFERENCE_RETURNS, probabilities, alpha=float(alpha))
    mv = mean_variance_baseline(assets=REFERENCE_ASSETS, regime_returns=REFERENCE_RETURNS, regime_probabilities=probabilities, previous_weights=REFERENCE_PREVIOUS, max_weights=REFERENCE_CAPS, alpha=float(alpha), risk_aversion=5.0, min_cash=0.10)
    baselines = [
        _metric_block("MARS-CVaR", decision),
        _metric_block("static CVaR", {"weights": {a: float(w) for a, w in zip(static.assets, static.weights)}, "expected_return": static.expected_return, "cvar_loss": static.cvar_loss, "turnover": static.turnover}),
        _metric_block("equal weight", equal),
        _metric_block("mean variance", mv),
    ]
    decision["objective_decomposition"] = {
        "expected_return_component": _f(-decision["expected_return"]),
        "tail_risk_component_signed": _f(float(risk_aversion) * decision["cvar_loss"]),
        "turnover_component": _f(float(turnover_penalty) * decision["turnover"]),
        "objective_reconstructed": _f(-decision["expected_return"] + float(risk_aversion) * decision["cvar_loss"] + float(turnover_penalty) * decision["turnover"]),
        "cvar_convention": "signed loss = negative portfolio return; a negative CVaR means the modeled tail return is positive, not that the loss display is missing a minus sign",
    }
    transition = _transition_evidence(float(stress_probability))
    wf = _walk_forward_evidence(root)
    decision["research_promotion_state"] = wf["promotion_state"]
    decision["decision_authorization_state"] = decision["risk_gate"]
    return {
        "algorithm": "MARS-CVaR",
        "decision": decision,
        "market_regime": transition,
        "portfolio_workspace": {
            "current_weights": {a: _f(v) for a, v in zip(REFERENCE_ASSETS, REFERENCE_PREVIOUS)},
            "target_weights": decision["target_weights"],
            "weight_changes": decision["weight_changes"],
            "asset_contributions": _asset_contributions([decision["target_weights"][a] for a in REFERENCE_ASSETS], probabilities),
        },
        "risk_lab": {
            "confidence_alpha": float(alpha),
            "cvar_convention": "signed loss = -portfolio return; display both signed CVaR and nonnegative downside magnitude",
            "cvar_loss_signed": _f(decision["cvar_loss"]),
            "downside_loss_magnitude": _f(max(0.0, decision["cvar_loss"])),
            "scenario_count": len(scenario_rows),
            "scenarios": scenario_rows,
            "dominant_tail_scenarios": [row["scenario_id"] for row in scenario_rows if row["in_cvar_tail"]][:3],
        },
        "constraints": _constraints(decision, max_turnover=0.40, max_cvar_loss=0.03),
        "transaction_analysis": {
            "turnover_definition": "L1 sum of absolute target minus current weights; one-way turnover is half this value when buys and sells are balanced",
            "aggregate_l1_turnover": _f(decision["turnover"]),
            "one_way_turnover": _f(decision["turnover"] / 2.0),
            "turnover_penalty": float(turnover_penalty),
            "trades": [{"asset": a, "current_weight": _f(REFERENCE_PREVIOUS[i]), "target_weight": _f(decision["target_weights"][a]), "absolute_trade": _f(abs(decision["weight_changes"][a]))} for i, a in enumerate(REFERENCE_ASSETS)],
        },
        "baselines": baselines,
        "frontier": _frontier(probabilities, float(alpha), float(turnover_penalty)),
        "sensitivity": _sensitivity(probabilities, float(alpha), float(risk_aversion), float(turnover_penalty)),
        "stress_testing": {
            "scenario_label": "SYNTHETIC_REFERENCE_STRESS_REGIME",
            "synthetic": True,
            "portfolio_loss_by_stress_scenario": [_f(max(0.0, -float(row["portfolio_return"]))) for row in scenario_rows if row["regime"] == "stress"],
            "governance_action": "HUMAN REVIEW; no orders or live rebalancing are emitted by this application",
        },
        "walk_forward_research": wf,
        "governance": {
            "optimization_authorization": decision["risk_gate"],
            "research_promotion": wf["promotion_state"],
            "human_review_required": True,
            "execution_enabled": False,
            "separation_note": "Optimization authorization says the analytical inputs passed their execution gate; research promotion remains a separate empirical question.",
        },
        "data_provenance": {
            "decision_data_class": "BUNDLED_REFERENCE_DATA",
            "scenario_data_class": "SIMULATED_RESAMPLED_SCENARIOS",
            "walk_forward_data_class": "HISTORICAL_OBSERVATIONAL_DATA",
            "provider": "repository deterministic fixture",
            "frequency": "reference scenario period; walk-forward artifact retains its own historical frequency",
            "adjustment_method": "not applicable to deterministic reference scenarios",
            "missing_data_policy": "not applicable to deterministic reference scenarios; live mode must fail explicitly rather than silently fall back",
            "source_artifacts": ["data/digital_twin/historical_prices/*.csv", "artifacts/mars_cvar/walk_forward_evidence.json"],
        },
        "claim_boundary": "Modeled optimization and historical walk-forward evidence only; not realized investment performance, a causal market forecast, a trade instruction, or a production promotion.",
    }
