AURUM PRODUCT V1
Signature algorithm: MARS-CVaR

WINDOWS COMMANDS
----------------
.\RUN_ACCEPTANCE.cmd          engineering/math/release gate
.\RUN_PRODUCT_ACCEPTANCE.cmd  product-runtime and HTTP gate
.\RUN_DEMO.cmd                deterministic portfolio demo and evidence
.\RUN_APP.cmd                 interactive institutional research workstation

Product URL: http://127.0.0.1:8811/
Evidence: AURUM\artifacts\product_runtime\latest_product_evidence.json

VALIDATION STATE
----------------
Engineering regression: 37 selected tests passed in the build environment
Product runtime acceptance: PASS
MARS-CVaR release evidence: PASS
Enterprise readiness contract: READY_FOR_HUMAN_REVIEW
Release manifest verification: PASS (68/68 files; secret/VCS hygiene clean)
Evidence bundle export: PASS (portable, hash-linked, retention-aware)
Software bill of materials: PASS (CycloneDX 1.5; 121 pinned components)
Walk-forward promotion state: RESEARCH_ONLY
Frontend command center: PASS (responsive, interactive, evidence-linked)
AURUM Intelligence: PASS (CIO brief, risk challenge, Ask AURUM)
AI default mode: LOCAL_GROUNDED (no external data transmission)
Governed live data: REFERENCE_ONLY (fail-closed; no optimizer feed enabled)
AI evaluation: PASS (6/6 grounding and safety contract checks)
Model validation: READY_FOR_INDEPENDENT_REVIEW (not an approval)
Enterprise platform: INTEGRATION_READY_NOT_PRODUCTION
Deployment preflight: research boundary PASS; production gate BLOCKED at 11/12
until immutable production image digests and deployment-owned controls are approved

The product surface preserves the repository-native MARS-CVaR LP and adds
regime, portfolio, risk, baseline, stress, provenance, governance, and AI
intelligence views. The AI layer interprets the current evidence payload; it
does not change solver outputs or authorize execution.
Modeled, synthetic, simulated, historical, optimized, and realized evidence
remain distinct. Human review is required; no orders are emitted.

Enterprise control-plane endpoints are available from the API:
  /v1/platform/readiness
  /v1/platform/observability
  /v1/platform/role-policy
  /v1/platform/audit/lineage
  /v1/platform/deployment-preflight
  /v1/platform/data-status
  /v1/platform/model-validation
  /v1/platform/enterprise-status
  /v1/platform/ai-evaluation

The product-facing AI endpoints are also available from the runtime:
  /api/ai/status
  /api/ai/brief
  /api/ai/ask?question=...
These are read-only integration contracts. Production SSO/RBAC, tenant
isolation, immutable storage, alerting, retention, image provenance, secret
injection, recovery, independent model review, and change approval remain
deployment/customer controls.
