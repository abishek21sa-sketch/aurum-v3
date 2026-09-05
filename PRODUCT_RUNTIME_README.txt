AURUM - Quantitative Risk and Portfolio Intelligence - Product Runtime

COMMANDS
--------
RUN_ACCEPTANCE.cmd          Engineering, mathematical, and release gate.
RUN_APP.cmd                 Launch the institutional research workstation.
RUN_DEMO.cmd                Regenerate deterministic evidence and launch it.
RUN_PRODUCT_ACCEPTANCE.cmd  Verify evidence sections and HTTP lifecycle.

PRODUCT SURFACE
---------------
URL: http://127.0.0.1:8811/
Evidence artifact: AURUM/artifacts/product_runtime/latest_product_evidence.json
Stop the app with Ctrl+C in its command window.

The runtime exposes market/regime, portfolio, CVaR risk, baseline and
walk-forward research, stress/frontier, provenance, and AURUM Intelligence
views. Its controls are governed inputs to a deterministic offline reference
fixture. The AURUM Intelligence workspace provides an evidence-grounded CIO
brief, risk challenge, and Ask AURUM question loop.

AI endpoints:
  /api/ai/status             active provider mode and safety boundary
  /api/ai/brief              current evidence-grounded CIO brief
  /api/ai/ask?question=...   bounded read-only question response

The default AI mode is LOCAL_GROUNDED: no portfolio data leaves the runtime.
An external model overlay requires explicit operator configuration and never
changes solver outputs, authorizes orders, or promotes research.

ENTERPRISE CONTROL CONTRACT
---------------------------
The API also exposes read-only integration contracts:
  /v1/platform/readiness       artifact/data-quality/governance gate
  /v1/platform/observability   low-cardinality operations health
  /v1/platform/role-policy     declarative IAM capability contract
  /v1/platform/audit/lineage   SHA-256 evidence lineage
  /v1/platform/evidence-bundle portable evidence export contract
  /v1/platform/data-status      governed live-data and freshness contract
  /v1/platform/model-validation independent-review packet
  /v1/platform/enterprise-status deployment/customer control ownership
  /v1/platform/ai-evaluation    AI grounding and safety contract checks
Readiness is for human review, not investment approval. The current build is
RESEARCH_ONLY and execution_enabled=false.

The repository includes docker-compose.production.yml as a deployment
contract. It is intentionally parameterized for immutable image digests and
external secrets; the production gate remains blocked until an operator
supplies deployment-owned values and approvals.

The release gate also writes:
  AURUM/artifacts/product_runtime/enterprise_evidence_bundle.json
The bundle is suitable for export to immutable enterprise storage. Retention,
access logging, legal hold, and destruction approval must be enforced by the
deployment platform.

CLAIM BOUNDARY
--------------
Optimization authorization is separate from research/alpha promotion.
The current promotion state remains RESEARCH_ONLY. The application does not
send orders, rebalance live accounts, or claim realized investment results.
