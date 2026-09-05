# AURUM Disaster Recovery Contract

This document defines the minimum recovery evidence and procedure for an
organization operating AURUM. Exact RTO and RPO values are organization-owned
service-level objectives and must be approved before production deployment.

## Recovery objectives

- Define and approve an RTO and RPO for the API, dashboard, evidence store,
  database, and cache separately.
- Treat decision evidence, release manifests, SBOMs, lineage records, and
  approval records as durable records, not disposable container state.
- Store exports in immutable, access-logged storage with retention and legal
  hold controls appropriate to the organization.

## Recovery procedure

1. Declare the incident and freeze promotion or downstream execution.
2. Identify the last approved release fingerprint and compatible SBOM.
3. Restore database and evidence-store backups into an isolated environment.
4. Restore the repository release and verify the release manifest, schemas,
   evidence bundle, and deployment preflight before starting services.
5. Run `/health`, `/v1/platform/readiness`, and the acceptance suite.
6. Reconcile decision IDs, run IDs, lineage hashes, and retained artifacts.
7. Obtain independent operational and risk approval before reopening access.

## Recovery testing

Run a documented restore drill at the organization’s approved cadence. Capture
the start/end time, restored release fingerprint, backup age, data-loss
assessment, acceptance output, exceptions, and sign-offs. A restore drill that
cannot reproduce the approved evidence chain is a failed drill and blocks
promotion.
