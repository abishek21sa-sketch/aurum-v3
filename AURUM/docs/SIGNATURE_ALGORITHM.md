# MARS CVaR Signature Algorithm

MARS-CVaR is AURUM's project-specific mathematical center: Markov regime
dynamics, next-regime probability evidence, regime-conditioned scenarios,
convex optimization, CVaR downside treatment, transaction costs, and portfolio
policy constraints.

For assets `j`, the LP keeps the following decision variables explicit:

- `w[j] >= 0`: target portfolio weight;
- `eta`: VaR threshold;
- `u[k,s] >= 0`: scenario excess loss;
- `d_plus[j], d_minus[j] >= 0`: positive and negative turnover decomposition.

The objective is equivalent in meaning to:

```text
minimize  -mu^T w + lambda * CVaR_alpha(loss) + tau * sum_j(d_plus[j] + d_minus[j])
```

subject to portfolio sum, position caps, scenario excess-loss constraints,
turnover decomposition, cash, and any other enabled policy constraints. The
implementation uses `scipy.optimize.linprog` with the HiGHS backend.

## Regime evidence

Regime transitions are represented by a row-stochastic Laplace-smoothed matrix.
The current state is used to derive the estimated next-regime vector; the
offline product also exposes a separate operator-controlled probability vector
for governed counterfactuals. A Markov regime model is descriptive evidence,
not causal proof of market behavior.

## Loss convention

Internally, loss is `-portfolio_return`, so a negative signed CVaR means the
modeled tail return is positive. The product surface labels this convention and
also reports a nonnegative downside-loss magnitude. Percentages are display
values; the optimizer uses decimal returns and weights.

## Evidence and governance

The decision bridge emits current and target weights, scenario count, solver
backend, parameters, gates, and a stable decision ID. The product evidence
assembler adds scenario-tail attribution, asset contributions, constraints,
stress/frontier sweeps, baselines, walk-forward results, and data provenance.

Optimization authorization is separate from alpha promotion. The current
historical evidence may correctly remain `RESEARCH_ONLY`; the runtime never
changes that state to make an upgrade appear successful.
