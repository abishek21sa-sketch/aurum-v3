# AURUM Product Runtime

The product runtime is a lightweight local HTTP surface over the native
MARS-CVaR implementation. It is intentionally offline-first so acceptance
does not depend on network data or credentials.

## Commands

From the extracted outer `AURUM_PRODUCT_V1` folder:

```text
RUN_PRODUCT_ACCEPTANCE.cmd  Verify the product surface, evidence, and HTTP lifecycle
RUN_APP.cmd                 Launch the interactive workstation
RUN_DEMO.cmd                Regenerate deterministic evidence and launch
```

The surface is served at `http://127.0.0.1:8811/`. The machine-readable
payload is `AURUM/artifacts/product_runtime/latest_product_evidence.json`.

## Workstation views

The runtime provides separate views for market/regime evidence, portfolio
construction, CVaR scenarios, research baselines and walk-forward validation,
stress/counterfactual sweeps, frontiers, and evidence/provenance. The
parameter controls are governed inputs to a deterministic reference fixture;
they do not issue trades.

## Governance and claim boundary

`AUTHORIZED` means the analytical decision gate passed. It does not mean the
strategy has earned alpha promotion. Research promotion remains an independent
state and is expected to remain `RESEARCH_ONLY` unless the evidence gate says
otherwise. Modeled, synthetic, simulated, historical, optimized, and realized
evidence classes remain distinct.
