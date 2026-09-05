"""
AURUM CVaR LP Optimizer

Rockafellar-Uryasev CVaR reformulation using cvxpy.

Minimizes:
    alpha + 1 / ((1 - beta) * N) * sum(u_i)

Subject to:
    u_i >= L_i(w) - alpha
    u_i >= 0
    sum(w) = 1
    bounds / long-only constraints
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

import cvxpy as cp
import numpy as np
import pandas as pd

from src.config.storage_paths import artifact_path, ensure_storage_dirs

ensure_storage_dirs()


@dataclass
class CVaRLPResult:
    status: str
    beta: float
    alpha_var: float
    cvar_objective: float
    expected_return: float
    volatility: float
    sharpe: float
    weights: Dict[str, float]
    method: str = "Rockafellar-Uryasev CVaR LP via cvxpy"


class CVaRLPOptimizer:
    def __init__(
        self,
        returns: pd.DataFrame,
        beta: float = 0.95,
        long_only: bool = True,
        max_weight: Optional[float] = None,
        min_return: Optional[float] = None,
    ):
        if returns.empty:
            raise ValueError("Returns DataFrame is empty.")

        self.returns = returns.dropna()
        self.assets = list(self.returns.columns)
        self.beta = beta
        self.long_only = long_only
        self.max_weight = max_weight
        self.min_return = min_return

        if not 0.0 < beta < 1.0:
            raise ValueError("beta must be between 0 and 1.")

    def optimize(self) -> CVaRLPResult:
        r = self.returns.values
        n_obs, n_assets = r.shape

        w = cp.Variable(n_assets)
        alpha = cp.Variable()
        u = cp.Variable(n_obs)

        portfolio_returns = r @ w
        portfolio_losses = -portfolio_returns

        objective = cp.Minimize(
            alpha + (1.0 / ((1.0 - self.beta) * n_obs)) * cp.sum(u)
        )

        constraints = [
            u >= portfolio_losses - alpha,
            u >= 0,
            cp.sum(w) == 1,
        ]

        if self.long_only:
            constraints.append(w >= 0)

        if self.max_weight is not None:
            constraints.append(w <= self.max_weight)

        if self.min_return is not None:
            mean_returns = self.returns.mean().values
            constraints.append(mean_returns @ w >= self.min_return)

        problem = cp.Problem(objective, constraints)

        try:
            problem.solve(solver=cp.CLARABEL)
        except Exception:
            problem.solve(solver=cp.SCS)

        if w.value is None:
            raise RuntimeError(f"CVaR LP optimization failed. Status: {problem.status}")

        weights = np.asarray(w.value).flatten()
        weights = np.maximum(weights, 0) if self.long_only else weights
        weights = weights / weights.sum()

        port_returns = self.returns.values @ weights
        expected_return = float(np.mean(port_returns) * 252)
        volatility = float(np.std(port_returns) * np.sqrt(252))
        sharpe = expected_return / volatility if volatility > 0 else 0.0

        result = CVaRLPResult(
            status=str(problem.status),
            beta=self.beta,
            alpha_var=float(alpha.value),
            cvar_objective=float(problem.value),
            expected_return=expected_return,
            volatility=volatility,
            sharpe=float(sharpe),
            weights={asset: float(weight) for asset, weight in zip(self.assets, weights)},
        )

        self.save_result(result)
        return result

    @staticmethod
    def save_result(result: CVaRLPResult) -> None:
        output_path = artifact_path("optimization", "cvar_lp_optimizer_result.json")
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=4)


def load_sample_returns() -> pd.DataFrame:
    np.random.seed(42)

    assets = ["SPY", "QQQ", "DIA", "TLT", "GLD", "BTC-USD", "ETH-USD"]
    n = 750

    means = np.array([0.00035, 0.00045, 0.00030, 0.00015, 0.00020, 0.00080, 0.00100])
    vols = np.array([0.010, 0.013, 0.009, 0.007, 0.008, 0.035, 0.045])

    returns = np.random.normal(means, vols, size=(n, len(assets)))
    return pd.DataFrame(returns, columns=assets)


def main() -> None:
    returns = load_sample_returns()

    optimizer = CVaRLPOptimizer(
        returns=returns,
        beta=0.95,
        long_only=True,
        max_weight=0.35,
    )

    result = optimizer.optimize()

    print("=" * 80)
    print("AURUM CVaR LP OPTIMIZER")
    print("=" * 80)
    print(f"Status:          {result.status}")
    print(f"Method:          {result.method}")
    print(f"Beta:            {result.beta}")
    print(f"VaR Alpha:       {result.alpha_var:.6f}")
    print(f"CVaR Objective:  {result.cvar_objective:.6f}")
    print(f"Expected Return: {result.expected_return:.4f}")
    print(f"Volatility:      {result.volatility:.4f}")
    print(f"Sharpe:          {result.sharpe:.4f}")
    print("-" * 80)
    for asset, weight in result.weights.items():
        print(f"{asset:<10} {weight:.4f}")
    print("=" * 80)


if __name__ == "__main__":
    main()