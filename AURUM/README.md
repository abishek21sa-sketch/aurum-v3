# AURUM Quantitative Risk and Portfolio Intelligence

AURUM is a human-gated quantitative portfolio research workstation. Its
signature decision system is MARS-CVaR: Markov regime evidence, probability-
weighted return scenarios, a convex CVaR linear program, turnover penalties,
and explicit portfolio constraints.

The repository ships with an offline deterministic reference fixture so the
product and acceptance checks do not require network access. Optional live
market-data integrations remain separate from the reference path and must
report provenance explicitly. This application does not send orders, rebalance
accounts, or promote a strategy to production.

## Product surfaces

The interactive runtime exposes:

- market and regime evidence, including transition-matrix validation,
  persistence, frequencies, and next-regime probabilities;
- current-versus-target portfolio construction with expected contributions,
  position limits, cash, and turnover constraints;
- CVaR scenario/tail diagnostics and an explicit signed-loss convention;
- governed stress and counterfactual sweeps across stress probability,
  confidence, risk weight, and turnover penalty;
- baseline comparison for MARS-CVaR, static CVaR, equal weight, and mean
  variance;
- chronological walk-forward evidence and multiple-testing-aware promotion;
- machine-readable decision evidence with solver, parameter, provenance, and
  claim-boundary fields.
- deterministic CycloneDX software bill of materials for the pinned Python
  dependency set.

The API also exposes read-only enterprise control contracts:

- `/v1/platform/readiness` for artifact integrity, data quality, provenance,
  model controls, and governance separation;
- `/v1/platform/observability` for low-cardinality operational health;
- `/v1/platform/role-policy` for deployment IAM capabilities;
- `/v1/platform/audit/lineage` for SHA-256 hash-linked evidence lineage.
- `/v1/platform/evidence-bundle` for portable evidence export with retention
  and storage-control metadata.

These contracts are integration surfaces, not a substitute for production
SSO/RBAC, immutable retention, alerting, change management, or trade controls.

## Windows commands

From the extracted outer `AURUM_PRODUCT_V1` folder:

```text
RUN_PRODUCT_ACCEPTANCE.cmd  Product-runtime and HTTP acceptance gate
RUN_ACCEPTANCE.cmd          Engineering, mathematical, and release gate
RUN_DEMO.cmd                Deterministic reference demo and runtime
RUN_APP.cmd                 Interactive runtime
```

The product opens at `http://127.0.0.1:8811/`. The latest evidence payload is
written to `artifacts/product_runtime/latest_product_evidence.json`.
The supply-chain inventory is written to
`artifacts/compliance/sbom.json` by the acceptance gate.

## Mathematical center

The executable formulation is in `src/optimization/signature_algorithm.py`
and the governed bridge is in
`src/institutional/mars_cvar_decision_bridge.py`. The LP keeps portfolio
weights, VaR threshold, CVaR excess variables, and positive/negative turnover
decomposition explicit. See `docs/SIGNATURE_ALGORITHM.md` and
`docs/RESEARCH_VALIDATION_MARS_CVAR.md` for the validation contract.

## Evidence discipline

Optimization authorization and research promotion are separate states. A
decision can be `AUTHORIZED` for analytical execution while the empirical
strategy remains `RESEARCH_ONLY`. Historical walk-forward results are research
evidence, not realized investment performance or a guarantee of future return.

## Synthetic AI/ML development lab

The repository also ships a deterministic 10,000-row synthetic scenario
dataset for feature engineering, edge-case coverage, replay, and transparent
ML mathematics. Run RUN_ACCEPTANCE.cmd to regenerate it and execute the
chronological ridge-regression and nearest-centroid baselines. The artifacts
are artifacts/synthetic/synthetic_ml_dataset.csv,
artifacts/synthetic/synthetic_ml_dataset_manifest.json, and
artifacts/synthetic/synthetic_ml_validation.json.

The dataset includes normal, trend, volatility-cluster, stress, recovery,
liquidity-shock, regime-boundary, missing-feature, stale-timestamp, duplicate,
outlier, nonpositive-price, label-noise, and schema-drift cases. It is marked
SIMULATED_SYNTHETIC_DATA, never enables the optimizer feed, and must not be
described as live-market, historical, customer, causal, or realized-performance
evidence.

The synthetic status contract is available at /v1/platform/synthetic-ml-status;
the product runtime exposes /api/synthetic-ml/status.

## Public data evidence lane

The project also supports a separate public-data intake path for authoritative
research inputs. `scripts/ingest_public_data.py` captures SEC EDGAR company
facts, FDIC BankFind institution records, U.S. Treasury Fiscal Data, and an
optional one-year public market-price snapshot through the existing research
adapter. Every captured artifact is hashed in
`artifacts/public_data/public_data_manifest.json` and exposed read-only at
`/v1/platform/public-data-status` and `/api/public-data/status`.

Public snapshots are real public records, not customer evidence. They remain
`RESEARCH_ONLY`; they do not enable the optimizer feed, prove realized returns,
or replace customer-owned controls. FRED is intentionally not fetched by
default because its official API requires an API key. Run the intake only when
network access is explicitly available and review the source URLs and
timestamps in the manifest before using any snapshot.

The public-source registry points to SEC EDGAR APIs
(https://www.sec.gov/search-filings/edgar-application-programming-interfaces),
FDIC BankFind API/bulk data
(https://banks.data.fdic.gov/bankfind-suite/bulkData), and Treasury Fiscal Data
(https://fiscaldata.treasury.gov/). These links are source documentation, not
claims that the project has customer authorization or production entitlements.
