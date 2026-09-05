# MARS-CVaR Governance Evidence

Evidence class: deterministic synthetic formulation/behavior evidence.

## Calibrated reference
- Turnover penalty: 0.0500
- Turnover: 0.363750
- CVaR signed loss: -0.003821 (negative means the modeled tail return is positive)
- CVaR downside magnitude: 0.000000
- Expected return: 0.004574
- Risk gate: AUTHORIZED

## Ablation
Removing effective turnover calibration (penalty=0.0002) produces turnover 0.900000, which breaches the 0.40 institutional turnover gate.

## Baselines
- Static-CVaR turnover: 0.363750; CVaR signed loss: -0.003821
- Equal-weight turnover: 0.200000; CVaR signed loss: 0.010450

## Claim boundary
This evidence tests formulation behavior and governance gates on a deterministic synthetic scenario. It does not establish investment alpha, calibrated regime forecasts, or realized performance.
