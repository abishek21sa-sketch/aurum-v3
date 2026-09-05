# Live data, AI, and validation readiness

This release separates three things that are often incorrectly collapsed into
one control: data acquisition, AI interpretation, and model promotion.

## Governed data contract

The default mode is `REFERENCE_ONLY`. To request live or paper data, the
deployment must set `AURUM_MARKET_DATA_MODE`, choose an approved provider, and
provide a snapshot containing every configured ticker with valid positive
prices and timestamps inside the freshness SLA. The contract fails closed on
missing, duplicate, malformed, or stale rows.

`AURUM_LIVE_DATA_APPROVED=true` is a separate approval flag. Passing data
quality alone does not enable the optimizer feed.

The status contract is available at `/v1/platform/data-status` and is also
written to `artifacts/compliance/live_data_status.json` by the acceptance run.

## AI provider contract

AURUM Intelligence uses local grounded reasoning by default. A live model is
opt-in and requires explicit provider, live-enable, external-transmission
approval, and managed API-key configuration. The model receives a compact
decision context and can only return interpretation; it cannot change solver
outputs, authorize execution, or promote research.

## Independent validation packet

`src/institutional/model_validation.py` runs reproducible internal checks for
no-lookahead, null-hypothesis presence, comparator coverage, transaction-cost
awareness, scenario lineage, CVaR convention, provenance, and governance
separation. A passing packet means `READY_FOR_INDEPENDENT_REVIEW`, never
independent approval. The packet is available at
`/v1/platform/model-validation` and is retained as
`artifacts/compliance/model_validation.json`.

## Promotion boundary

The optimizer may be analytically authorized while research promotion remains
`RESEARCH_ONLY`. Independent validation, live-data approval, human committee
review, and deployment-owned controls are separate gates.
