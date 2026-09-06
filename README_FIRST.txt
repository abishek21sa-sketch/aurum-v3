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
Engineering regression: 46 selected tests passed in the build environment
Product runtime acceptance: PASS
MARS-CVaR release evidence: PASS
Enterprise readiness contract: READY_FOR_HUMAN_REVIEW
Release evidence: PASS (77/77 checks; secret/VCS hygiene clean)
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
Deployment preflight: research boundary PASS; production gate BLOCKED at 13/14
until immutable production image digests are supplied and deployment-owned controls
are approved
Unified control plane: 6/6 repository controls covered; deployment 13/14;
customer acceptance 0/5 (customer configuration required)
Customer evidence register: 5 enterprise controls + 5 operational evidence
items, all explicitly owned and currently REQUIRED/approval-gated

EXTERNAL EVIDENCE INTAKE
------------------------
Customer-owned evidence is never fabricated or committed. Before a deployment
acceptance run, point the process at real, approved manifests:
  $env:AURUM_CUSTOMER_EVIDENCE_FILE = "C:\\secure\\customer_evidence.json"
  $env:AURUM_PRODUCTION_PROVENANCE_FILE = "C:\\secure\\production_image_provenance.json"
Use AURUM\\config\\customer_evidence.example.json and
AURUM\\config\\production_image_provenance.example.json as shape templates.
Each customer control needs an evidence URI, SHA-256, approver, UTC approval
timestamp, and verification record. Image provenance additionally needs a
signed attestation and sha256-pinned references for all four production images.
The intake validates shape and metadata locally; customer authority and
independent verification remain external responsibilities.

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
  /v1/platform/control-plane
  /v1/platform/operations-status
  /v1/platform/customer-evidence
  /v1/platform/image-provenance

The product-facing AI endpoints are also available from the runtime:
  /api/ai/status
  /api/ai/brief
  /api/ai/ask?question=...
These are read-only integration contracts. Production SSO/RBAC, tenant
isolation, immutable storage, alerting, retention, image provenance, secret
injection, recovery, independent model review, and change approval remain
deployment/customer controls.
