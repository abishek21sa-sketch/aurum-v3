# MARS-CVaR

MARS-CVaR is AURUM's governed regime-aware portfolio allocation layer. It estimates a Laplace-smoothed Markov transition matrix, converts the current state into next-regime probabilities, weights regime-conditioned return scenarios, and solves a long-only CVaR linear program with turnover costs.

The objective is `-expected_return + lambda * CVaR_alpha + tau * turnover`, subject to full investment, position caps, optional minimum cash, CVaR excess-loss constraints, and exact L1 turnover decomposition.

`src/institutional/mars_cvar_decision_bridge.py` converts the mathematical solution into a deterministic auditable decision artifact with a risk gate. The artifact is optimization evidence only; it is not a claim of realized alpha, future returns, or causal market prediction.


## Institutional governance
The decision bridge applies both a CVaR-loss gate and a turnover gate. An LP solution can therefore be mathematically optimal while still being blocked from promotion when the implied rebalance is operationally excessive.

The deterministic reference calibration evaluates turnover penalties from `0.0` through `0.10`. In the current synthetic validation case, penalties through `0.02` still imply 70-90% L1 turnover; `0.05` is the first tested penalty satisfying the 0.40 turnover ceiling, producing 0.36375 turnover. This is a reference calibration result, not a universal transaction-cost estimate.

## Baselines and ablation
Validation publishes an equal-weight baseline, a static-regime CVaR baseline, and a turnover-governance ablation. The ablation deliberately removes effective turnover control to demonstrate whether the governance component changes the decision. Full sensitivity is retained in `artifacts/mars_cvar/turnover_sensitivity.csv`.

## Evidence boundary
All current MARS-CVaR release evidence is deterministic synthetic formulation/behavior evidence. It does not establish investment alpha, calibrated regime forecasts, market causality, or realized portfolio performance.
