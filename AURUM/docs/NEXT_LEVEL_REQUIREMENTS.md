# Next-Level Readiness Requirements

This is the honest release checklist for moving from a strong research product
to a system that a large regulated organization could evaluate. Green items are
implemented in the repository or in its deterministic acceptance path. Open
items require deployment evidence, customer authorization, or independent
review; they cannot be manufactured by adding more synthetic rows.

## Current status

| Workstream | Current evidence | Remaining requirement |
| --- | --- | --- |
| Mathematical correctness | LP, CVaR, turnover, constraints, solver status, tests | Independent implementation review and numerical stress suite |
| Research validity | Walk-forward, baselines, promotion gate | Frozen holdout, confidence intervals, multiple-testing correction, replication |
| ML engineering | Synthetic edge-case lab, chronological baselines, manifests | Real authorized datasets, calibration, drift, uncertainty, model cards |
| AI safety | Local grounded mode, bounded overlay, evidence boundary | Red-team evaluation, prompt-injection tests, output monitoring, provider review |
| Data | Public-source intake and hash-linked manifests | Entitlements, freshness SLOs, reconciliation, outage drills, customer data controls |
| Security | Configuration and role-policy contracts | SSO/OIDC/SAML, secrets management, encryption, scanning, penetration testing |
| Operations | Readiness, observability, audit, evidence bundle contracts | On-call ownership, alert routing, SLO/RTO/RPO proof, restore drills |
| Governance | Human review, disabled execution, research-only promotion | Signed approvals, change control, model-risk committee, retirement process |
| Product | Decision workspace, Intelligence, Research Operations, export | Accessibility, browser matrix, user research, support model, release cadence |
| Supply chain | Pinned requirements, SBOM, release fingerprint | Signed builds, artifact attestation, dependency policy, vulnerability response |

## Highest-value next work

1. Create a versioned data contract for each authorized live provider and test
   freshness, completeness, reconciliation, and failover behavior.
2. Freeze a final time-based holdout and have an independent reviewer reproduce
   the MARS-CVaR result from the evidence bundle.
3. Add scenario capacity and transaction-cost models using approved market
   microstructure data rather than reference assumptions.
4. Build a red-team suite for prompt injection, unsupported claims, data leakage,
   malformed provider output, and model outage behavior.
5. Deploy identity, tenant isolation, immutable audit retention, key rotation,
   and least-privilege role mapping in a controlled environment.
6. Add signed release provenance, vulnerability scanning, rollback rehearsal,
   and a documented incident/change-management process.
7. Run a design-partner pilot with explicit success criteria, support ownership,
   and a review board that can reject promotion.

## Release decision rule

The product should remain research-only until the open controls above have
authentic evidence and an accountable approver. A passing local test suite is a
necessary engineering signal, not a substitute for customer, security,
operations, regulatory, or independent model-validation evidence.
