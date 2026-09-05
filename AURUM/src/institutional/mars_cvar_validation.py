from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np

from src.optimization.signature_algorithm import MARSCVaRResult, solve_mars_cvar


@dataclass(frozen=True)
class PortfolioDiagnostics:
    expected_return: float
    cvar_loss: float
    turnover: float


def _scenario_stack(
    assets: Sequence[str],
    regime_returns: Mapping[str, np.ndarray],
    regime_probabilities: Mapping[str, float],
) -> tuple[np.ndarray, np.ndarray]:
    n = len(assets)
    rows: list[np.ndarray] = []
    probs: list[float] = []
    for regime, pr in regime_probabilities.items():
        arr = np.asarray(regime_returns[regime], dtype=float)
        if arr.ndim != 2 or arr.shape[1] != n:
            raise ValueError(f"bad return matrix for {regime}")
        for row in arr:
            rows.append(row)
            probs.append(float(pr) / len(arr))
    q = np.asarray(probs, dtype=float)
    if not np.isclose(q.sum(), 1.0):
        raise ValueError("scenario probabilities must sum to one")
    return np.asarray(rows, dtype=float), q


def weighted_cvar(losses: np.ndarray, probs: np.ndarray, alpha: float) -> float:
    order = np.argsort(losses)
    losses = np.asarray(losses, dtype=float)[order]
    probs = np.asarray(probs, dtype=float)[order]
    remaining = 1.0 - alpha
    tail = remaining
    total = 0.0
    for loss, prob in zip(losses[::-1], probs[::-1]):
        take = min(float(prob), remaining)
        total += float(loss) * take
        remaining -= take
        if remaining <= 1e-12:
            break
    return total / tail


def evaluate_weights(
    weights: Sequence[float],
    previous_weights: Sequence[float],
    assets: Sequence[str],
    regime_returns: Mapping[str, np.ndarray],
    regime_probabilities: Mapping[str, float],
    *,
    alpha: float = 0.95,
) -> PortfolioDiagnostics:
    w = np.asarray(weights, dtype=float)
    prev = np.asarray(previous_weights, dtype=float)
    R, q = _scenario_stack(assets, regime_returns, regime_probabilities)
    mu = q @ R
    return PortfolioDiagnostics(
        expected_return=float(mu @ w),
        cvar_loss=float(weighted_cvar(-(R @ w), q, alpha)),
        turnover=float(np.abs(w - prev).sum()),
    )


def static_regime_probabilities(regimes: Sequence[str]) -> dict[str, float]:
    if not regimes:
        raise ValueError("regimes cannot be empty")
    p = 1.0 / len(regimes)
    return {r: p for r in regimes}


def equal_weight_baseline(
    assets: Sequence[str],
    previous_weights: Sequence[float],
    regime_returns: Mapping[str, np.ndarray],
    regime_probabilities: Mapping[str, float],
    *,
    alpha: float = 0.95,
) -> dict:
    n = len(assets)
    diag = evaluate_weights(np.full(n, 1.0 / n), previous_weights, assets, regime_returns, regime_probabilities, alpha=alpha)
    return {"name": "equal_weight", "weights": {a: 1.0 / n for a in assets}, **asdict(diag)}


def run_turnover_calibration(
    *,
    assets: Sequence[str],
    regime_returns: Mapping[str, np.ndarray],
    regime_probabilities: Mapping[str, float],
    previous_weights: Sequence[float],
    max_weights: Sequence[float],
    penalties: Sequence[float],
    alpha: float,
    risk_aversion: float,
    min_cash: float,
    max_turnover: float,
) -> list[dict]:
    rows: list[dict] = []
    for penalty in penalties:
        result = solve_mars_cvar(
            assets,
            regime_returns,
            regime_probabilities,
            previous_weights,
            max_weights=max_weights,
            alpha=alpha,
            risk_aversion=risk_aversion,
            turnover_penalty=float(penalty),
            min_cash=min_cash,
        )
        rows.append({
            "turnover_penalty": float(penalty),
            "expected_return": result.expected_return,
            "cvar_loss": result.cvar_loss,
            "turnover": result.turnover,
            "passes_turnover_gate": bool(result.turnover <= max_turnover + 1e-12),
            "weights": {a: float(w) for a, w in zip(result.assets, result.weights)},
        })
    return rows


def static_cvar_baseline(
    *,
    assets: Sequence[str],
    regime_returns: Mapping[str, np.ndarray],
    previous_weights: Sequence[float],
    max_weights: Sequence[float],
    alpha: float,
    risk_aversion: float,
    turnover_penalty: float,
    min_cash: float,
) -> MARSCVaRResult:
    return solve_mars_cvar(
        assets,
        regime_returns,
        static_regime_probabilities(list(regime_returns)),
        previous_weights,
        max_weights=max_weights,
        alpha=alpha,
        risk_aversion=risk_aversion,
        turnover_penalty=turnover_penalty,
        min_cash=min_cash,
    )

def mean_variance_baseline(
    *, assets: Sequence[str], regime_returns: Mapping[str,np.ndarray], regime_probabilities: Mapping[str,float],
    previous_weights: Sequence[float], max_weights: Sequence[float], alpha: float=.95, risk_aversion: float=5.0,
    min_cash: float=0.0, cash_asset: str='CASH',
) -> dict:
    """Long-only mean-variance comparator evaluated on the same weighted scenario set."""
    from scipy.optimize import minimize
    R,q=_scenario_stack(assets,regime_returns,regime_probabilities); mu=q@R
    centered=R-mu; cov=(centered.T*q)@centered
    n=len(assets); bounds=[(0,float(max_weights[i])) for i in range(n)]
    cons=[{'type':'eq','fun':lambda w: float(np.sum(w)-1.0)}]
    if cash_asset in assets and min_cash>0:
        ci=list(assets).index(cash_asset); cons.append({'type':'ineq','fun':lambda w,ci=ci: float(w[ci]-min_cash)})
    f=lambda w: float(-(mu@w)+risk_aversion*(w@cov@w))
    res=minimize(f,np.full(n,1/n),method='SLSQP',bounds=bounds,constraints=cons,options={'maxiter':1000,'ftol':1e-12})
    if not res.success: raise RuntimeError(f'mean-variance baseline failed: {res.message}')
    diag=evaluate_weights(res.x,previous_weights,assets,regime_returns,regime_probabilities,alpha=alpha)
    return {'name':'mean_variance','weights':{a:float(w) for a,w in zip(assets,res.x)},**asdict(diag)}
