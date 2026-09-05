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
Engineering regression: 27 selected tests passed in the build environment
Product runtime acceptance: PASS
MARS-CVaR release evidence: PASS
Enterprise readiness contract: READY_FOR_HUMAN_REVIEW
Release manifest verification: PASS (39/39 files; secret/VCS hygiene clean)
Evidence bundle export: PASS (portable, hash-linked, retention-aware)
Software bill of materials: PASS (CycloneDX 1.5; 121 pinned components)
Walk-forward promotion state: RESEARCH_ONLY
Deployment preflight: research boundary PASS; production gate BLOCKED until
deployment-owned controls are implemented and approved

The product surface preserves the repository-native MARS-CVaR LP and adds
regime, portfolio, risk, baseline, stress, provenance, and governance views.
Modeled, synthetic, simulated, historical, optimized, and realized evidence
remain distinct. Human review is required; no orders are emitted.

Enterprise control-plane endpoints are available from the API:
  /v1/platform/readiness
  /v1/platform/observability
  /v1/platform/role-policy
  /v1/platform/audit/lineage
  /v1/platform/deployment-preflight
These are read-only integration contracts. Production SSO/RBAC, immutable
storage, alerting, retention, image provenance, secret injection, recovery,
and change approval remain deployment controls.
