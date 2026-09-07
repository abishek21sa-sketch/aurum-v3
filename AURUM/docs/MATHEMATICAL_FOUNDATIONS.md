# AURUM Mathematical Foundations

This document describes the mathematical contracts implemented by AURUM. It
is explicit about what is computed, what is estimated, and what the result
cannot prove.

## 1. Notation and decision object

Let there be n assets, S scenarios, and a current portfolio w0.

- wj: proposed target weight for asset j.
- rsj: decimal return of asset j in scenario s.
- Rs(w) = sum(j) rsj * wj: portfolio return in scenario s.
- Ls(w) = -Rs(w): signed portfolio loss convention.
- ps: scenario probability, with ps >= 0 and sum(s) ps = 1.
- eta: VaR threshold used by the CVaR linear program.
- us: nonnegative excess-loss variable for scenario s.
- alpha: confidence level, for example 0.95.
- lambda: CVaR risk weight.
- tau: turnover penalty.

The product stores decimal values in the engine and formats percentages only at
the display boundary. Every decision artifact records parameters, solver,
scenario count, and input lineage.

## 2. Markov regime evidence

The regime component starts with transition counts Nij from state i to state j.
Laplace smoothing gives:

~~~text
Pij = (Nij + kappa) / (sum_l Nil + kappa * K)
~~~

K is the number of regimes and kappa is a positive smoothing constant. Each
row sums to one. If the current regime distribution is qt, the next-regime
evidence is:

~~~text
q(t+1) = qt * P
~~~

The product also supports an operator-controlled next-regime stress vector for
counterfactual analysis. That vector is a governed scenario input, not a claim
that the Markov process has forecast the market.

## 3. Regime-conditioned return scenarios

For each regime k, the scenario generator supplies an asset-return vector
r(k,s) or a resampled historical/reference vector. A probability-weighted
expected return is:

~~~text
muj = sum_s ps * rsj
~~~

The scenario matrix is retained rather than reduced to a mean and covariance
only. This makes tail attribution and stress sweeps inspectable. Scenario class
and data class are stored in the evidence payload so a reviewer can distinguish
public, reference, and synthetic data.

## 4. Convex CVaR linear program

The optimization objective is:

~~~text
minimize  -mu^T w
          + lambda * [ eta + 1/(1-alpha) * sum_s ps * us ]
          + tau * sum_j (d_plus_j + d_minus_j)
~~~

subject to the scenario excess-loss constraints:

~~~text
us >= Ls(w) - eta
us >= 0
~~~

and portfolio/turnover constraints:

~~~text
sum_j wj = 1
wj >= 0
wj <= upper_bound_j
wj - w0j = d_plus_j - d_minus_j
d_plus_j >= 0
d_minus_j >= 0
~~~

Additional cash, position, group, or policy constraints can be enabled through
the governed bridge. Since Ls(w) is affine in w and all penalties are linear,
the problem is a linear program. A feasible optimum is solved with the HiGHS
backend through scipy.optimize.linprog.

### Why the CVaR term is linear

For a fixed eta, expected excess loss is the weighted average of
max(Ls - eta, 0). The variables us represent those maxima using linear
inequalities. Minimizing the objective makes each us equal to the smallest
feasible excess loss. The optimizer therefore computes the discrete
Rockafellar-Uryasev CVaR representation without a nonlinear solver.

## 5. Signed loss and downside display

AURUM uses loss = -return internally. Therefore a negative signed CVaR means
the modeled tail return is positive under the recorded convention. The UI also
reports a nonnegative downside-loss magnitude so the sign cannot be silently
misread. A reviewer should inspect both the convention and the scenario-tail
table before interpreting a number.

## 6. Turnover and implementation friction

The decomposition

~~~text
wj - w0j = d_plus_j - d_minus_j
~~~

with nonnegative variables makes the L1 turnover quantity explicit:

~~~text
turnover = sum_j (d_plus_j + d_minus_j)
~~~

The tau parameter discourages unnecessary movement from the current portfolio.
It is a mathematical friction proxy, not a full market-impact or broker cost
model. Slippage, spread, market impact, borrow, taxes, liquidity, and order
scheduling remain separate required extensions.

## 7. Walk-forward validation

The research validator preserves time order:

1. Fit or estimate only on an earlier window.
2. Freeze the decision rule and parameters for the next window.
3. Evaluate the frozen rule on that later window.
4. Advance the window and repeat.

The resulting out-of-sample sequence is compared with static CVaR, equal-weight,
and mean-variance baselines. A model is not promoted because it has a single
attractive period. The current promotion contract checks completeness,
look-ahead status, minimum sample size, and incremental baseline uplift.

## 8. Statistical controls and limitations

The repository reports sample size, chronological coverage, returns, volatility,
drawdown-style quantities, and baseline comparisons. These are evidence
descriptors, not guarantees. A production validation program still needs:

- frozen evaluation windows and an untouched final holdout;
- confidence intervals and dependence-aware uncertainty estimates;
- multiple-testing correction across the research search space;
- realistic transaction-cost, liquidity, and capacity models;
- parameter sensitivity and perturbation analysis;
- independent replication by a reviewer who did not author the strategy;
- documented model-risk approval and retirement criteria.

## 9. Numerical and audit invariants

Acceptance checks assert, where applicable:

- probabilities are finite, nonnegative, and normalized;
- portfolio weights satisfy the configured sum and bounds;
- scenario and feature rows preserve their declared schema;
- no future timestamp is used by a prior training window;
- solver status is recorded rather than inferred from a display value;
- decision IDs, artifact hashes, source timestamps, and configuration values are
  retained in evidence lineage.

The mathematical result is reproducible only together with its inputs,
parameters, software version, solver backend, and evidence hash.
