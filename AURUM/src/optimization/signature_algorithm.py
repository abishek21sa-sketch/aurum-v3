from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence
import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class MARSCVaRResult:
    assets: tuple[str, ...]
    weights: np.ndarray
    objective: float
    expected_return: float
    cvar_loss: float
    turnover: float
    status: str
    regime_probabilities: dict[str, float]


def laplace_transition_matrix(states: Sequence[str], state_order: Sequence[str], smoothing: float = 1.0) -> np.ndarray:
    order = list(state_order)
    if not order or len(set(order)) != len(order):
        raise ValueError("state_order must contain unique states")
    if smoothing <= 0 or not np.isfinite(smoothing):
        raise ValueError("smoothing must be a positive finite value")
    idx = {s: i for i, s in enumerate(order)}
    counts = np.full((len(order), len(order)), float(smoothing))
    for a, b in zip(states[:-1], states[1:]):
        if a in idx and b in idx:
            counts[idx[a], idx[b]] += 1.0
    return counts / counts.sum(axis=1, keepdims=True)


def next_regime_probabilities(states: Sequence[str], state_order: Sequence[str], smoothing: float = 1.0) -> dict[str, float]:
    if not states:
        raise ValueError("states cannot be empty")
    order = list(state_order)
    if states[-1] not in order:
        raise ValueError("current state not present in state_order")
    p = laplace_transition_matrix(states, order, smoothing)
    row = p[order.index(states[-1])]
    return {s: float(row[i]) for i, s in enumerate(order)}


def _weighted_cvar(losses: np.ndarray, probs: np.ndarray, alpha: float) -> float:
    order = np.argsort(losses)
    losses = losses[order]
    probs = probs[order]
    tail = 1.0 - alpha
    remaining = tail
    total = 0.0
    for loss, prob in zip(losses[::-1], probs[::-1]):
        take = min(float(prob), remaining)
        total += float(loss) * take
        remaining -= take
        if remaining <= 1e-12:
            break
    return total / tail


def solve_mars_cvar(
    assets: Sequence[str],
    regime_returns: Mapping[str, np.ndarray],
    regime_probabilities: Mapping[str, float],
    previous_weights: Sequence[float],
    *,
    alpha: float = 0.95,
    risk_aversion: float = 1.0,
    turnover_penalty: float = 0.001,
    max_weights: Sequence[float] | None = None,
    min_cash: float = 0.0,
    cash_asset: str = "CASH",
) -> MARSCVaRResult:
    assets = tuple(assets)
    n = len(assets)
    prev = np.asarray(previous_weights, dtype=float)
    if prev.shape != (n,):
        raise ValueError("previous_weights length mismatch")
    if n == 0 or not np.all(np.isfinite(prev)):
        raise ValueError("assets and previous_weights must be non-empty and finite")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")

    regimes = list(regime_returns)
    if not regimes or set(regimes) != set(regime_probabilities):
        raise ValueError("regime returns and probabilities must contain the same non-empty regimes")
    rp = np.asarray([regime_probabilities[r] for r in regimes], dtype=float)
    if np.any(~np.isfinite(rp)) or np.any(rp < 0) or not np.isclose(rp.sum(), 1.0):
        raise ValueError("regime probabilities must be nonnegative and sum to 1")

    scenarios, probs = [], []
    for regime, pr in zip(regimes, rp):
        arr = np.asarray(regime_returns[regime], dtype=float)
        if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[1] != n or not np.all(np.isfinite(arr)):
            raise ValueError(f"bad return matrix for {regime}")
        for row in arr:
            scenarios.append(row)
            probs.append(float(pr) / len(arr))
    R = np.asarray(scenarios, dtype=float)
    q = np.asarray(probs, dtype=float)
    mu = q @ R
    m = len(q)

    # variables: w[n], eta[1], u[m], dplus[n], dminus[n]
    off_eta = n
    off_u = n + 1
    off_dp = off_u + m
    off_dm = off_dp + n
    N = off_dm + n
    c = np.zeros(N)
    c[:n] = -mu
    c[off_eta] = risk_aversion
    c[off_u:off_u+m] = risk_aversion * q / (1-alpha)
    c[off_dp:off_dp+n] = turnover_penalty
    c[off_dm:off_dm+n] = turnover_penalty

    Aeq = []
    beq = []
    row = np.zeros(N); row[:n] = 1.0
    Aeq.append(row); beq.append(1.0)
    for j in range(n):
        row = np.zeros(N)
        row[j] = 1.0; row[off_dp+j] = -1.0; row[off_dm+j] = 1.0
        Aeq.append(row); beq.append(prev[j])

    Aub = []
    bub = []
    for s in range(m):
        # u_s >= -R_s w - eta  => -R_s w - eta - u_s <= 0
        row = np.zeros(N)
        row[:n] = -R[s]
        row[off_eta] = -1.0
        row[off_u+s] = -1.0
        Aub.append(row); bub.append(0.0)
    if cash_asset in assets and min_cash > 0:
        row = np.zeros(N); row[assets.index(cash_asset)] = -1.0
        Aub.append(row); bub.append(-min_cash)

    caps = np.ones(n) if max_weights is None else np.asarray(max_weights, dtype=float)
    bounds = [(0.0, float(caps[j])) for j in range(n)] + [(None, None)] + [(0.0, None)]*m + [(0.0, None)]*(2*n)
    res = linprog(c, A_ub=np.asarray(Aub), b_ub=np.asarray(bub), A_eq=np.asarray(Aeq), b_eq=np.asarray(beq), bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"MARS-CVaR optimization failed: {res.message}")
    w = res.x[:n]
    losses = -(R @ w)
    cvar = _weighted_cvar(losses, q, alpha)
    turnover = float(np.abs(w-prev).sum())
    return MARSCVaRResult(assets, w, float(res.fun), float(mu @ w), float(cvar), turnover, "OPTIMAL", {r: float(regime_probabilities[r]) for r in regimes})
