# Fortune-50 customer readiness packet

This document is the handoff checklist for a design partner, security team,
and investment-governance committee. It intentionally distinguishes evidence
already produced by the repository from controls that must be proven in the
customer deployment.

## Product evidence already available

- MARS-CVaR decision, CVaR convention, constraints, stress/frontier views, and
  walk-forward evidence.
- Evidence-grounded AURUM Intelligence brief and bounded Ask AURUM endpoint.
- Hash-linked release manifest, SBOM, evidence bundle, deployment preflight,
  live-data quality contract, and model-validation packet.
- Research-only execution boundary: no orders, broker integration, or live
  promotion capability is enabled.

## Required enterprise acceptance evidence

1. SSO/OIDC or SAML integration, role mapping, break-glass access, and
   segregation-of-duties tests.
2. Tenant isolation, encryption, key rotation, access logging, retention,
   legal hold, and deletion-approval tests where multiple customers share a
   deployment.
3. Immutable image-digest attestation, vulnerability scanning, signed release
   provenance, and controlled rollback evidence.
4. Live-market-data provider entitlements, freshness/error budgets, outage
   behavior, reconciliation, and a human approval record before optimizer use.
5. Independent model validation, documented limitations, adverse scenarios,
   transaction-cost review, and committee sign-off.
6. Approved SLO/RTO/RPO, monitoring and alert routing, incident response,
   backup/restore drill, support ownership, and change-management records.

## Supplying external evidence

The repository cannot create customer approvals. Supply authentic records
through process-local environment variables:

```powershell
$env:AURUM_CUSTOMER_EVIDENCE_FILE = "C:\\secure\\customer_evidence.json"
$env:AURUM_PRODUCTION_PROVENANCE_FILE = "C:\\secure\\production_image_provenance.json"
$env:AURUM_OPERATIONS_CONFIG_FILE = "C:\\secure\\operations.json"
.\RUN_ACCEPTANCE.cmd
```

Use the two `config/*.example.json` files for the required shape. The intake
requires a URI, SHA-256, approver, UTC approval timestamp, and verification
record for each customer control. Image provenance also requires a signed
attestation and digest-pinned references for every production image. Results
appear in the control plane and compliance artifacts, while the original
customer records stay out of Git.

## Pilot exit criteria

A pilot is not complete until the customer can reproduce a decision ID and
evidence bundle, trace every input to a source and timestamp, answer the AI
brief with cited grounding, demonstrate that execution remains disabled, and
complete a documented restore and incident drill.
