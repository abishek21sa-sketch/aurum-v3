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
Each snapshot receives a provider-neutral normalized receipt with a request ID,
received timestamp, ticker set, and payload SHA-256. Receipts are secret-free
and support replay, reconciliation, and audit correlation without coupling the
core product to a vendor SDK.

## AI provider contract

AURUM Intelligence uses local grounded reasoning by default. A live model is
opt-in and requires explicit provider, live-enable, external-transmission
approval, and managed API-key configuration. A separate live-evaluation flag
is required before a control-plane evaluation may call that provider. The model
receives a compact decision context and can only return interpretation; it
cannot change solver outputs, authorize execution, or promote research.

## Independent validation packet

`src/institutional/model_validation.py` runs reproducible internal checks for
no-lookahead, null-hypothesis presence, comparator coverage, transaction-cost
awareness, scenario lineage, CVaR convention, provenance, and governance
separation. A passing packet means `READY_FOR_INDEPENDENT_REVIEW`, never
independent approval. The packet is available at
`/v1/platform/model-validation` and is retained as
`artifacts/compliance/model_validation.json`.

## Control-plane and operations contracts

`/v1/platform/control-plane` reports repository, deployment, and customer
acceptance coverage using separate denominators. `/v1/platform/operations-status`
reports the customer-owned SLO, RTO/RPO, retention, support, alerting,
backup/restore, and change-management fields. The default operations result is
`CUSTOMER_CONFIGURATION_REQUIRED` until those values are approved and
evidenced by the deployment owner.

## Promotion boundary

The optimizer may be analytically authorized while research promotion remains
`RESEARCH_ONLY`. Independent validation, live-data approval, human committee
review, and deployment-owned controls are separate gates.

## External evidence intake

Customer acceptance evidence and production image provenance are intentionally
out-of-band. Set `AURUM_CUSTOMER_EVIDENCE_FILE` and
`AURUM_PRODUCTION_PROVENANCE_FILE` to customer/deployment-owned JSON manifests
before running acceptance. The repository includes
`config/customer_evidence.example.json` and
`config/production_image_provenance.example.json` as non-authoritative shape
templates; the real manifests must not be committed with secrets or private
customer records.

The customer manifest covers `identity.sso`, `identity.rbac_enforcement`,
`tenancy.isolation`, `evidence.immutable_storage`, and
`operations.slo_and_support`. Each record requires an evidence URI, the
SHA-256 of the underlying evidence, an approver, a UTC approval timestamp, and
a verification record. The provenance manifest requires signed attestation
metadata plus `@sha256:` references for `AURUM_REDIS_IMAGE`,
`AURUM_TIMESCALE_IMAGE`, `AURUM_API_IMAGE`, and `AURUM_DASHBOARD_IMAGE`.
`/v1/platform/customer-evidence` and `/v1/platform/image-provenance` expose
the read-only validation results. Shape validation is not independent trust;
the customer and deployment owner remain responsible for authenticity.
