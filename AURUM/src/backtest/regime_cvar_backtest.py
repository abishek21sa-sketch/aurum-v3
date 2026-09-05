"""
AURUM Regime-Filtered CVaR Backtest

Compares three strategies from 2018-01-01 to 2025-01-01:
  1. SPY Buy & Hold (benchmark)
  2. Equal Weight (SPY, QQQ, TLT, GLD) rebalanced monthly
  3. Regime-Filtered CVaR (our strategy)

Walk-forward methodology:
  - 252-day training window
  - Rebalance every 21 trading days
  - HMM regime detection on training window
  - CVaR optimization with regime-adjusted constraints
  - No lookahead bias

Output:
  results/backtest/regime_cvar_backtest_results.json
  results/backtest/regime_cvar_backtest_tearsheet.txt

Run:
    python -m src.backtest.regime_cvar_backtest
"""

from __future__ import annotations

import json
import warnings
warnings.filterwarnings("ignore")

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "digital_twin" / "historical_prices"
RESULTS_DIR = ROOT / "results" / "backtest"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_prices() -> pd.DataFrame:
    """Load and align price data for all assets."""
    assets = ["SPY", "QQQ", "TLT", "GLD"]
    dfs = {}
    for asset in assets:
        path = DATA_DIR / f"{asset}.csv"
        df = pd.read_csv(path, parse_dates=["date"])
        df = df.set_index("date")["close"].rename(asset)
        dfs[asset] = df

    prices = pd.DataFrame(dfs).dropna()
    prices.index = pd.to_datetime(prices.index)
    prices = prices.sort_index()
    return prices


def detect_regime(returns: pd.DataFrame) -> str:
    """
    Simple rule-based regime detection on a returns window.
    Returns: 'bull', 'bear', 'high_vol', or 'normal'

    Uses:
    - Rolling volatility (annualized)
    - Recent trend (last 20 days vs 60 days)
    - Max drawdown over window
    """
    spy_returns = returns["SPY"].dropna()

    if len(spy_returns) < 20:
        return "normal"

    # Annualized volatility
    vol = spy_returns.std() * np.sqrt(252)

    # Trend: recent 20-day return vs 60-day
    recent_return = spy_returns.iloc[-20:].sum()
    longer_return = spy_returns.iloc[-60:].sum() if len(spy_returns) >= 60 else recent_return

    # Drawdown
    cum = (1 + spy_returns).cumprod()
    rolling_max = cum.cummax()
    drawdown = ((cum - rolling_max) / rolling_max).min()

    # Regime rules
    if vol > 0.25 or drawdown < -0.15:
        return "high_vol"
    elif recent_return > 0.02 and longer_return > 0.03:
        return "bull"
    elif recent_return < -0.02 and longer_return < -0.02:
        return "bear"
    else:
        return "normal"


def get_regime_weights(regime: str) -> dict[str, float]:
    """
    Regime-based target weights — defensive posture in stress, aggressive in bull.
    These are the CONSTRAINTS passed to the optimizer.
    """
    if regime == "bull":
        return {"SPY": 0.40, "QQQ": 0.35, "TLT": 0.15, "GLD": 0.10}
    elif regime == "bear":
        return {"SPY": 0.15, "QQQ": 0.10, "TLT": 0.50, "GLD": 0.25}
    elif regime == "high_vol":
        return {"SPY": 0.20, "QQQ": 0.10, "TLT": 0.45, "GLD": 0.25}
    else:  # normal
        return {"SPY": 0.30, "QQQ": 0.25, "TLT": 0.30, "GLD": 0.15}


def optimize_cvar(
    returns: pd.DataFrame,
    max_weights: dict[str, float],
    beta: float = 0.95,
) -> np.ndarray:
    """
    Minimize CVaR using Rockafellar-Uryasev LP formulation via cvxpy.
    Falls back to max_weights if optimization fails.
    """
    try:
        import cvxpy as cp

        r = returns.values
        n_obs, n_assets = r.shape

        w = cp.Variable(n_assets)
        alpha = cp.Variable()
        u = cp.Variable(n_obs)

        losses = -r @ w
        objective = cp.Minimize(alpha + (1.0 / ((1 - beta) * n_obs)) * cp.sum(u))

        constraints = [
            u >= losses - alpha,
            u >= 0,
            cp.sum(w) == 1,
            w >= 0.05,  # min 5% per asset
        ]

        # Apply regime-based max weights
        assets = list(returns.columns)
        for i, asset in enumerate(assets):
            constraints.append(w[i] <= max_weights.get(asset, 0.50))

        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.CLARABEL, verbose=False)

        if w.value is not None:
            weights = np.maximum(w.value, 0)
            weights = weights / weights.sum()
            return weights

    except Exception:
        pass

    # Fallback to regime weights
    assets = list(returns.columns)
    fallback = np.array([max_weights.get(a, 0.25) for a in assets])
    return fallback / fallback.sum()


def calculate_metrics(
    returns: pd.Series,
    name: str,
) -> dict[str, Any]:
    """Calculate full tearsheet metrics for a return series."""
    r = returns.dropna()

    if len(r) == 0:
        return {}

    # Annualized return
    total_return = (1 + r).prod() - 1
    n_years = len(r) / 252
    annual_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0

    # Volatility
    annual_vol = r.std() * np.sqrt(252)

    # Sharpe (risk-free = 0 for simplicity)
    sharpe = annual_return / annual_vol if annual_vol > 0 else 0

    # Sortino
    downside = r[r < 0].std() * np.sqrt(252)
    sortino = annual_return / downside if downside > 0 else 0

    # Max drawdown
    cum = (1 + r).cumprod()
    rolling_max = cum.cummax()
    drawdowns = (cum - rolling_max) / rolling_max
    max_drawdown = drawdowns.min()

    # CVaR at 95%
    var_95 = np.percentile(r, 5)
    cvar_95 = r[r <= var_95].mean()

    # Calmar
    calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

    # Win rate
    win_rate = (r > 0).mean()

    return {
        "strategy": name,
        "total_return_pct": round(total_return * 100, 2),
        "annual_return_pct": round(annual_return * 100, 2),
        "annual_volatility_pct": round(annual_vol * 100, 2),
        "sharpe_ratio": round(sharpe, 3),
        "sortino_ratio": round(sortino, 3),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "cvar_95_pct": round(cvar_95 * 100, 2),
        "calmar_ratio": round(calmar, 3),
        "win_rate_pct": round(win_rate * 100, 2),
        "n_trading_days": len(r),
        "n_years": round(n_years, 1),
    }


def run_backtest(
    start_date: str = "2018-01-01",
    end_date: str = "2025-01-01",
    train_window: int = 252,
    rebalance_freq: int = 21,
) -> dict[str, Any]:
    """
    Main backtest engine.
    Returns results dict with equity curves and metrics.
    """
    print(f"Loading prices...")
    prices = load_prices()

    # Filter to backtest period (include training window before start)
    prices = prices[prices.index >= "2015-01-01"]
    returns = prices.pct_change().dropna()

    # Get trading days in backtest period
    backtest_returns = returns[
        (returns.index >= start_date) & (returns.index < end_date)
    ]
    trading_days = backtest_returns.index
    assets = list(prices.columns)

    print(f"Backtest period: {start_date} to {end_date}")
    print(f"Trading days: {len(trading_days)}")
    print(f"Assets: {assets}")

    # Initialize portfolio values
    spy_values = [1.0]
    eq_values = [1.0]
    cvar_values = [1.0]

    # Current weights
    eq_weights = np.array([0.25, 0.25, 0.25, 0.25])
    cvar_weights = np.array([0.25, 0.25, 0.25, 0.25])

    # Track regime history
    regime_history = []
    weight_history = []

    print(f"Running walk-forward backtest...")
    for i, day in enumerate(trading_days):

        # Get today's returns
        day_returns = backtest_returns.loc[day].values

        # SPY buy and hold
        spy_idx = assets.index("SPY")
        spy_values.append(spy_values[-1] * (1 + day_returns[spy_idx]))

        # Equal weight
        eq_daily = np.dot(eq_weights, day_returns)
        eq_values.append(eq_values[-1] * (1 + eq_daily))

        # CVaR strategy
        cvar_daily = np.dot(cvar_weights, day_returns)
        cvar_values.append(cvar_values[-1] * (1 + cvar_daily))

        # Rebalance on schedule
        if i % rebalance_freq == 0:
            # Get training window (data before this day, no lookahead)
            train_end_idx = returns.index.get_loc(day)
            train_start_idx = max(0, train_end_idx - train_window)
            train_returns = returns.iloc[train_start_idx:train_end_idx]

            if len(train_returns) >= 60:
                # Detect regime
                regime = detect_regime(train_returns)
                regime_history.append({"date": str(day.date()), "regime": regime})

                # Get regime weights
                max_w = get_regime_weights(regime)

                # Optimize CVaR
                cvar_weights = optimize_cvar(train_returns, max_w)

                weight_history.append({
                    "date": str(day.date()),
                    "regime": regime,
                    "weights": {
                        assets[j]: round(float(cvar_weights[j]), 4)
                        for j in range(len(assets))
                    }
                })

                if i % 252 == 0:
                    print(f"  {day.date()} | Regime: {regime:8s} | "
                          f"SPY:{cvar_weights[0]:.2f} "
                          f"QQQ:{cvar_weights[1]:.2f} "
                          f"TLT:{cvar_weights[2]:.2f} "
                          f"GLD:{cvar_weights[3]:.2f}")

    # Build return series
    dates = [trading_days[0]] + list(trading_days)
    spy_series = pd.Series(spy_values, index=dates).pct_change().dropna()
    eq_series = pd.Series(eq_values, index=dates).pct_change().dropna()
    cvar_series = pd.Series(cvar_values, index=dates).pct_change().dropna()

    # Calculate metrics
    print("Calculating metrics...")
    spy_metrics = calculate_metrics(spy_series, "SPY Buy & Hold")
    eq_metrics = calculate_metrics(eq_series, "Equal Weight")
    cvar_metrics = calculate_metrics(cvar_series, "Regime CVaR")

    # Equity curves for charting
    equity_curves = []
    for i, day in enumerate(trading_days):
        equity_curves.append({
            "date": str(day.date()),
            "spy": round(spy_values[i + 1], 6),
            "equal_weight": round(eq_values[i + 1], 6),
            "regime_cvar": round(cvar_values[i + 1], 6),
            "regime": regime_history[i // rebalance_freq]["regime"]
            if i // rebalance_freq < len(regime_history) else "normal",
        })

    results = {
        "timestamp": utc_now(),
        "backtest_config": {
            "start_date": start_date,
            "end_date": end_date,
            "train_window_days": train_window,
            "rebalance_freq_days": rebalance_freq,
            "assets": assets,
            "beta_cvar": 0.95,
        },
        "metrics": {
            "spy": spy_metrics,
            "equal_weight": eq_metrics,
            "regime_cvar": cvar_metrics,
        },
        "regime_history": regime_history[-50:],
        "weight_history": weight_history[-20:],
        "equity_curves": equity_curves,
    }

    return results


def format_tearsheet(results: dict[str, Any]) -> str:
    """Generate a clean tearsheet text report."""
    cfg = results["backtest_config"]
    m = results["metrics"]

    lines = []
    lines.append("=" * 70)
    lines.append("AURUM REGIME-FILTERED CVaR BACKTEST — TEARSHEET")
    lines.append("=" * 70)
    lines.append(f"Period:      {cfg['start_date']} to {cfg['end_date']}")
    lines.append(f"Assets:      {', '.join(cfg['assets'])}")
    lines.append(f"Train window: {cfg['train_window_days']} days")
    lines.append(f"Rebalance:   Every {cfg['rebalance_freq_days']} trading days")
    lines.append("")
    lines.append(f"{'Metric':<28} {'SPY B&H':>12} {'Equal Wt':>12} {'Regime CVaR':>12}")
    lines.append("-" * 70)

    metrics_to_show = [
        ("Total Return", "total_return_pct", "%"),
        ("Annual Return", "annual_return_pct", "%"),
        ("Annual Volatility", "annual_volatility_pct", "%"),
        ("Sharpe Ratio", "sharpe_ratio", ""),
        ("Sortino Ratio", "sortino_ratio", ""),
        ("Max Drawdown", "max_drawdown_pct", "%"),
        ("CVaR 95%", "cvar_95_pct", "%"),
        ("Calmar Ratio", "calmar_ratio", ""),
        ("Win Rate", "win_rate_pct", "%"),
    ]

    for label, key, suffix in metrics_to_show:
        spy_val = m["spy"].get(key, 0)
        eq_val = m["equal_weight"].get(key, 0)
        cvar_val = m["regime_cvar"].get(key, 0)
        lines.append(
            f"{label:<28} {str(round(spy_val,2))+suffix:>12} "
            f"{str(round(eq_val,2))+suffix:>12} "
            f"{str(round(cvar_val,2))+suffix:>12}"
        )

    lines.append("=" * 70)
    lines.append("")
    lines.append("INTERPRETATION")
    lines.append("-" * 70)

    # Auto-generate interpretation
    cvar_sharpe = m["regime_cvar"].get("sharpe_ratio", 0)
    spy_sharpe = m["spy"].get("sharpe_ratio", 0)
    cvar_dd = m["regime_cvar"].get("max_drawdown_pct", 0)
    spy_dd = m["spy"].get("max_drawdown_pct", 0)
    cvar_ret = m["regime_cvar"].get("annual_return_pct", 0)
    spy_ret = m["spy"].get("annual_return_pct", 0)

    if cvar_sharpe > spy_sharpe:
        lines.append(f"+ Regime CVaR Sharpe ({cvar_sharpe:.2f}) beats SPY ({spy_sharpe:.2f})")
    else:
        lines.append(f"  Regime CVaR Sharpe ({cvar_sharpe:.2f}) vs SPY ({spy_sharpe:.2f})")

    if abs(cvar_dd) < abs(spy_dd):
        lines.append(f"+ Regime CVaR max drawdown ({cvar_dd:.1f}%) better than SPY ({spy_dd:.1f}%)")
    else:
        lines.append(f"  Regime CVaR max drawdown ({cvar_dd:.1f}%) vs SPY ({spy_dd:.1f}%)")

    lines.append(f"  Annual return: Regime CVaR {cvar_ret:.1f}% vs SPY {spy_ret:.1f}%")
    lines.append("=" * 70)

    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("AURUM REGIME-FILTERED CVaR BACKTEST")
    print("=" * 70)

    results = run_backtest(
        start_date="2018-01-01",
        end_date="2025-01-01",
        train_window=252,
        rebalance_freq=21,
    )

    # Save JSON results
    json_path = RESULTS_DIR / "regime_cvar_backtest_results.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Results saved: {json_path.relative_to(ROOT)}")

    # Save tearsheet
    tearsheet = format_tearsheet(results)
    txt_path = RESULTS_DIR / "regime_cvar_backtest_tearsheet.txt"
    txt_path.write_text(tearsheet, encoding="utf-8")
    print(f"Tearsheet saved: {txt_path.relative_to(ROOT)}")

    # Print tearsheet
    print()
    print(tearsheet)


if __name__ == "__main__":
    main()