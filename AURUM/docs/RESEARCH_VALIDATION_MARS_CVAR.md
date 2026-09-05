# MARS CVaR Research Validation Contract

## Falsification question

The null hypothesis is that next-regime weighting does not improve
risk-adjusted out-of-sample performance or tail loss relative to static CVaR,
equal weight, and mean variance after the same turnover-cost assumptions.

## Required evidence

- chronological walk-forward train, decision, and next-period evaluation
  windows with no future information in regime estimation, transitions, return
  estimates, covariance, or scenario construction;
- identical evaluation periods and cost assumptions for all baselines;
- metrics for return, volatility, Sharpe, downside risk, CVaR, drawdown,
  turnover, transaction cost, and concentration where implemented;
- ablations for regime conditioning, turnover penalty, CVaR tail term, and
  transition/smoothing assumptions where the data supports them;
- sensitivity and scalability evidence for `alpha`, risk weight, turnover
  penalty, asset count, regime count, scenario count, and walk-forward periods;
- a multiple-testing-aware promotion gate with a legitimate `RESEARCH_ONLY`
  outcome.

## Evidence classes

The repository separates observed market data, estimated regimes, simulated or
resampled scenarios, optimized portfolios, historical walk-forward results,
and realized live performance. The offline demo uses bundled deterministic
reference data and synthetic reference scenarios. Its walk-forward artifact is
historical research evidence. Neither is realized investment performance.

## Governance boundary

Optimization authorization answers whether the analytical inputs passed the
decision gate. Research promotion answers whether the strategy has earned a
status beyond research. These states are never conflated, and promotion
thresholds or backtests are not modified to obtain a green result.
