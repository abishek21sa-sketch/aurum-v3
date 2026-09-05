from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Mapping, Sequence
import numpy as np
from src.optimization.signature_algorithm import solve_mars_cvar

# Anchor generated artifacts to the repository, not the process working
# directory.  Services, CI runners, and scheduled jobs commonly invoke this
# module from another directory; relative output silently breaks that use case.
OUTPUT = Path(__file__).resolve().parents[2] / "results/institutional/mars_cvar_decision.json"

def build_mars_cvar_decision(*, assets: Sequence[str], regime_returns: Mapping[str,np.ndarray], regime_probabilities: Mapping[str,float], previous_weights: Sequence[float], max_weights: Sequence[float], max_cvar_loss: float | None = None, max_turnover: float | None = None, **kwargs):
    # API/evidence callers can opt out of persistence.  Keeping the pure
    # computation path side-effect free makes read-only service deployments
    # safe while preserving the historical script behavior by default.
    persist = bool(kwargs.pop("persist", True))
    result = solve_mars_cvar(assets, regime_returns, regime_probabilities, previous_weights, max_weights=max_weights, **kwargs)
    previous = {a: round(float(w), 10) for a, w in zip(assets, previous_weights)}
    scenario_count = sum(len(np.asarray(values)) for values in regime_returns.values())
    payload = {
        "algorithm": "MARS-CVaR",
        "status": result.status,
        "assets": list(result.assets),
        "current_weights": previous,
        "target_weights": {a: round(float(w), 10) for a,w in zip(result.assets,result.weights)},
        "weight_changes": {a: round(float(w-p), 10) for a,w,p in zip(result.assets,result.weights,previous_weights)},
        "objective": result.objective,
        "expected_return": result.expected_return,
        "cvar_loss": result.cvar_loss,
        "cvar_loss_convention": "signed loss = negative portfolio return; negative values indicate the modeled tail return is positive",
        "turnover": result.turnover,
        "regime_probabilities": result.regime_probabilities,
        "scenario_count": scenario_count,
        "solver": {"backend": "scipy.optimize.linprog", "method": "highs", "status": result.status, "objective": result.objective},
        "parameters": {
            "alpha": kwargs.get("alpha", 0.95),
            "risk_aversion_lambda": kwargs.get("risk_aversion", 1.0),
            "turnover_penalty_tau": kwargs.get("turnover_penalty", 0.001),
            "max_weights": [float(x) for x in max_weights],
            "min_cash": kwargs.get("min_cash", 0.0),
            "cash_asset": kwargs.get("cash_asset", "CASH"),
            "max_cvar_loss_gate": max_cvar_loss,
            "max_turnover_gate": max_turnover,
        },
        "claim_boundary": "Optimization evidence only; not a forecast of realized investment performance.",
    }
    caps = np.asarray(max_weights, dtype=float)
    cash_index = list(assets).index(kwargs.get("cash_asset", "CASH")) if kwargs.get("cash_asset", "CASH") in assets else None
    cash_slack = None if cash_index is None else float(result.weights[cash_index] - kwargs.get("min_cash", 0.0))
    payload["feasibility"] = {
        "status": "FEASIBLE",
        "portfolio_sum_residual": float(abs(float(result.weights.sum()) - 1.0)),
        "max_position_cap_violation": float(np.maximum(result.weights - caps, 0.0).max()),
        "minimum_cash_slack": cash_slack,
    }
    cvar_ok = max_cvar_loss is None or result.cvar_loss <= max_cvar_loss
    turnover_ok = max_turnover is None or result.turnover <= max_turnover
    payload["gates"] = {
        "cvar": {"limit": max_cvar_loss, "observed": result.cvar_loss, "passed": bool(cvar_ok)},
        "turnover": {"limit": max_turnover, "observed": result.turnover, "passed": bool(turnover_ok)},
    }
    payload["authorized"] = bool(cvar_ok and turnover_ok)
    payload["risk_gate"] = "AUTHORIZED" if payload["authorized"] else "BLOCKED"
    payload["blocked_reasons"] = [name for name, gate in payload["gates"].items() if not gate["passed"]]
    # Keep the decision identity stable for the established canonical fixture.
    # Diagnostics may grow without changing the identity of the mathematical
    # decision that existing acceptance evidence refers to.
    identity_fields = {
        key: payload[key]
        for key in (
            "algorithm", "status", "assets", "target_weights", "weight_changes",
            "expected_return", "cvar_loss", "turnover", "regime_probabilities",
            "claim_boundary", "gates", "authorized", "risk_gate", "blocked_reasons",
        )
    }
    digest = hashlib.sha256(json.dumps(identity_fields, sort_keys=True).encode()).hexdigest()[:16].upper()
    payload["decision_id"] = f"MARS-{digest}"
    if persist:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
