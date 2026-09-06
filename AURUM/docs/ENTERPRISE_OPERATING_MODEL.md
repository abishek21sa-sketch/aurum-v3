# AURUM Enterprise Operating Model

## Purpose

AURUM is an offline-first quantitative research workstation. This release
adds a machine-readable control-plane contract for enterprise integration
without claiming that the repository itself is an identity, execution, or
regulatory control system.

## Control-plane endpoints

The FastAPI surface exposes twelve read-only contracts:

| Endpoint | Purpose |
| --- | --- |
| `/v1/platform/readiness` | Artifact integrity, data-quality, provenance, model-control, and governance checks. |
| `/v1/platform/observability` | Low-cardinality health metrics safe for dashboards and alert rules. |
| `/v1/platform/role-policy` | Declarative role/capability contract for deployment IAM. |
| `/v1/platform/audit/lineage` | SHA-256 hash-linked lineage for fixture input, solver output, evidence, and release artifact. |
| `/v1/platform/evidence-bundle` | Portable evidence record with stable run identity, bundle hash, provenance, governance, and retention metadata. |
| `/v1/platform/deployment-preflight` | Fail-closed deployment, container, secret, ingress, recovery, and paper-trading boundary checks. |
| `/v1/platform/data-status` | Governed provider mode, snapshot freshness, ticker completeness, and optimizer-feed approval. |
| `/v1/platform/model-validation` | Reproducible internal checks prepared for independent model validation. |
| `/v1/platform/enterprise-status` | SSO, tenancy, immutable storage, SLO, and customer-owned integration status. |
| `/v1/platform/ai-evaluation` | Grounding, output-boundary, and external-transmission contract checks. |
| `/v1/platform/control-plane` | Unified six-area summary with separate repository, deployment, and customer denominators. |
| `/v1/platform/operations-status` | SLO, RTO/RPO, retention, support, alerting, recovery, and change-control status. |

The operations contract also emits a five-item customer evidence register.
Each item identifies its owner, required configuration fields, missing fields,
and `REQUIRED` or `EVIDENCED` status. This makes the remaining handoff work
machine-checkable without treating repository placeholders as customer approval.

`READY_FOR_HUMAN_REVIEW` means the evidence package is internally coherent.
It does not mean investment approval, research promotion, or authorization to
send an order.

The current preflight intentionally reports `research_gate=PASS` and
`production_gate=BLOCKED`. Repository-controlled secret injection, rootless
images, API health checks, and direct production-port exposure are represented
by a production compose profile. Immutable image digests and organization-
owned SSO/IAM still must be supplied and attested in the target environment.

## Control boundaries

- Optimization authorization and research promotion are separate states.
- The current build remains `RESEARCH_ONLY` and `execution_enabled=false`.
- Evidence is classified as bundled reference, simulated, or historical
  observational data; classes are not silently promoted.
- Missing-data behavior is explicit. Live acquisition must fail closed rather
  than silently substitute a fixture.
- Hashes make exported evidence tamper-evident. Deployment must add immutable
  storage, retention, access control, SSO/RBAC, alerting, and change approval.
- The role policy is descriptive. It is not a substitute for production IAM,
  segregation of duties, or an approval workflow.

## Recommended deployment controls

1. Put the API behind the organization’s SSO/API gateway and enforce the
   declared role policy at the gateway and service boundary.
2. Export readiness, lineage, and evidence payloads to immutable object
   storage with retention and access logging.
3. Alert on readiness `FAIL`, lineage root-hash changes, missing artifacts,
   stale walk-forward evidence, or any unexpected change to execution state.
4. Require a human approval record and independent risk review before any
   research promotion or integration with an execution system.
5. Keep live data credentials and broker integrations outside this research
   build; no secrets are required for the deterministic acceptance path.

## Supply-chain inventory

`scripts/generate_sbom.py` produces the deterministic CycloneDX 1.5 artifact
at `artifacts/compliance/sbom.json`. The current release records 121 pinned
components from `requirements.txt`, with PyPI package URLs and a source-file
hash. The SBOM is a dependency inventory, not a vulnerability verdict; an
organization’s software-composition-analysis service should consume it and
apply its own advisories, exceptions, and remediation workflow.

## Evidence export

`scripts/export_enterprise_evidence.py` writes
`artifacts/product_runtime/enterprise_evidence_bundle.json`. The bundle is
designed to cross a deployment boundary into immutable storage and review
queues. Its `run_id`, `decision_id`, `lineage_root_hash`, and `bundle_sha256`
allow consumers to correlate the record without trusting a mutable UI state.
