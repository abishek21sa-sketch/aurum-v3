# AURUM Operations Runbook

This runbook covers the deterministic research workstation and its deployment
boundary. The current release is `RESEARCH_ONLY` with `execution_enabled=false`.
It does not place orders, connect to a broker, or promote research into a live
strategy.

## Start and verify

From the `AURUM` directory:

```powershell
python scripts/run_deployment_preflight.py
python scripts/rc3_windows_acceptance.py
python scripts/verify_enterprise_release.py
```

The expected research result is `AURUM_DEPLOYMENT_PREFLIGHT=PASS`. A
`AURUM_PRODUCTION_GATE=BLOCKED` result is expected until the deployment-owned
controls listed by the preflight are implemented and approved.

## Service checks

- `GET /health` confirms API liveness.
- `GET /v1/platform/readiness` returns artifact, data-quality, provenance,
  governance, and release checks.
- `GET /v1/platform/observability` returns low-cardinality health signals.
- `GET /v1/platform/deployment-preflight` returns the fail-closed deployment
  boundary contract.
- `GET /v1/platform/data-status` returns provider mode, freshness, and
  optimizer-feed approval state.
- `GET /v1/platform/model-validation` returns the internal packet prepared for
  independent review.
- `GET /v1/platform/ai-evaluation` returns grounding and safety-contract
  checks for AURUM Intelligence.
- `GET /v1/platform/enterprise-status` returns SSO, tenancy, immutable
  storage, and customer-operations ownership state.
- `GET /v1/platform/audit/lineage` returns the hash-linked evidence lineage.
- `GET /v1/platform/evidence-bundle` returns the portable evidence bundle.

Never treat an HTTP 200 response as authorization to execute. Inspect
`research_promotion`, `execution_enabled`, and the production preflight gate.

## Incident response

1. Stop promotion and disable any downstream execution integration.
2. Preserve the release manifest, SBOM, preflight artifact, evidence bundle,
   logs, and the reported decision ID.
3. Compare the lineage root hash and artifact hashes with the approved release.
4. Record the incident, owner, timestamp, affected run IDs, and disposition in
   the organization’s incident system.
5. Re-run the acceptance and release verifier after remediation; require
   independent review before re-enabling any integration.

## Production prerequisites

The deployment team owns the remaining production controls: immutable image
digests, external secret management, non-root container enforcement,
authenticated ingress, SSO/RBAC, network policy, immutable evidence retention,
backup and restore, vulnerability management, monitoring, and change
approval. These controls must be tested in the target environment and are not
silently inferred from this repository.
