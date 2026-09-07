# AURUM v3

AURUM is a human-gated quantitative portfolio research and intelligence
workstation. It combines regime evidence, constrained portfolio optimization,
tail-risk analysis, chronological validation, grounded AI explanation, and
research-operations governance in one auditable product surface.

This repository is a consolidated successor to the earlier AURUM and AURUM V2
experiments. It keeps the strongest ideas from both while adding a governed
decision engine, deterministic offline acceptance, public-data provenance,
synthetic ML coverage, an AI research layer, and a research-operations loop.

## What is implemented

- MARS-CVaR: regime-conditioned scenarios, convex CVaR optimization, turnover
  penalties, position constraints, and explicit loss conventions.
- Chronological walk-forward evaluation with baseline comparison and a
  research-promotion gate.
- Grounded AURUM Intelligence with executive briefs, risk challenges,
  evidence-change conditions, and bounded questions against current evidence.
- A deterministic observe, validate, challenge, decide, learn research loop
  with Bull, Bear, Risk, and Judge roles.
- Public-data intake for SEC, FDIC, Treasury, and optional market snapshots,
  each with source timestamps and SHA-256 provenance.
- A 10,000-row synthetic ML laboratory for edge cases, replay, leakage checks,
  and transparent baseline mathematics.
- Fail-closed controls: no orders, no account rebalancing, and no silent
  promotion from research to production.

## Start here

1. Read AURUM/README.md for the product and Windows run commands.
2. Read AURUM/docs/MATHEMATICAL_FOUNDATIONS.md for the optimization and
   validation details.
3. Read AURUM/docs/AI_ML_SYSTEM.md for the grounded AI, synthetic data, and
   model-control design.
4. Read AURUM/docs/EVOLUTION_FROM_AURUM_V1_V2.md for the product comparison.
5. Read AURUM/docs/NEXT_LEVEL_REQUIREMENTS.md before treating this as a
   deployable institutional system.

## Verification

From the extracted project directory on Windows:

    RUN_PRODUCT_ACCEPTANCE.cmd
    RUN_ACCEPTANCE.cmd
    RUN_DEMO.cmd
    RUN_APP.cmd

The deterministic acceptance path is designed to run without network access.
Any live provider, model, customer evidence, or production deployment must be
enabled explicitly and must remain separately identifiable from reference and
synthetic evidence.

## Important boundary

The repository is research software, not an order-management system. A green
analytical gate means that the recorded inputs and computations satisfy the
repository checks; it does not establish realized performance, causal market
claims, customer authorization, regulatory approval, or production readiness.
