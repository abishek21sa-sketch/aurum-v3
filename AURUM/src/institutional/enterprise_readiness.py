"""Enterprise operating contracts for the AURUM research workstation.

The readiness payload is intentionally deterministic and read-only.  It gives
an operator, CI system, or control-plane integration a small contract for
artifact integrity, evidence quality, governance separation, and provenance.
It does not authenticate a user, authorize a trade, or promote research.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


READINESS_SCHEMA_VERSION = "1.0"
POLICY_SCHEMA_VERSION = "1.0"
REQUIRED_ARTIFACTS = (
    "src/institutional/mars_cvar_product.py",
    "src/institutional/mars_cvar_decision_bridge.py",
    "src/institutional/deployment_preflight.py",
    "src/optimization/signature_algorithm.py",
    "src/api/main.py",
    "scripts/product_adapter.py",
    "scripts/product_runtime.py",
    "scripts/product_frontend.py",
    "src/institutional/ai_intelligence.py",
    "src/institutional/live_data_contract.py",
    "src/institutional/live_data_ingestion.py",
    "src/institutional/model_validation.py",
    "src/institutional/enterprise_platform.py",
    "src/institutional/ai_evaluation.py",
    "src/institutional/control_plane.py",
    "src/institutional/operations_contract.py",
    "src/institutional/external_evidence.py",
    "src/institutional/synthetic_ml.py",
    "scripts/run_deployment_preflight.py",
    "scripts/generate_synthetic_ml_dataset.py",
    "scripts/run_synthetic_ml_validation.py",
    "artifacts/mars_cvar/walk_forward_evidence.json",
    "artifacts/mars_cvar/release_manifest.json",
    "artifacts/compliance/deployment_preflight.json",
    "artifacts/product_runtime/latest_ai_intelligence_brief.json",
    "artifacts/compliance/live_data_status.json",
    "artifacts/compliance/model_validation.json",
    "artifacts/compliance/enterprise_platform.json",
    "artifacts/compliance/ai_evaluation.json",
    "artifacts/compliance/control_plane.json",
    "artifacts/compliance/operations_status.json",
    "artifacts/compliance/customer_evidence_status.json",
    "artifacts/compliance/production_image_provenance_status.json",
    "artifacts/synthetic/synthetic_ml_dataset.csv",
    "artifacts/synthetic/synthetic_ml_dataset_manifest.json",
    "artifacts/synthetic/synthetic_ml_validation.json",
    "config/operations.json",
    "docker-compose.yml",
    "Dockerfile.api",
    "Dockerfile.dashboard",
    "docker-compose.production.yml",
    "configs/prod.yaml",
    "docs/OPERATIONS_RUNBOOK.md",
    "docs/DISASTER_RECOVERY.md",
    "docs/AI_INTELLIGENCE.md",
    "docs/LIVE_DATA_AND_VALIDATION.md",
    "docs/ENTERPRISE_CUSTOMER_READINESS.md",
    "schemas/aurum_readiness.schema.json",
    "schemas/aurum_role_policy.schema.json",
    "schemas/aurum_evidence_bundle.schema.json",
    "schemas/aurum_sbom.schema.json",
    "schemas/aurum_deployment_preflight.schema.json",
    "schemas/aurum_live_data.schema.json",
    "schemas/aurum_control_plane.schema.json",
    "schemas/aurum_operations.schema.json",
    "schemas/aurum_customer_evidence.schema.json",
    "schemas/aurum_production_image_provenance.schema.json",
    "schemas/aurum_synthetic_dataset_manifest.schema.json",
    "schemas/aurum_synthetic_ml_validation.schema.json",
    "config/customer_evidence.example.json",
    "config/production_image_provenance.example.json",
    "artifacts/compliance/sbom.json",
)


@dataclass(frozen=True)
class ReadinessCheck:
    """One machine-readable enterprise control result."""

    check_id: str
    domain: str
    status: str
    severity: str
    summary: str
    details: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "domain": self.domain,
            "status": self.status,
            "severity": self.severity,
            "summary": self.summary,
            "details": dict(self.details),
        }


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return _hash_bytes(encoded)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _artifact_inventory(root: Path) -> tuple[list[dict[str, Any]], list[ReadinessCheck]]:
    inventory: list[dict[str, Any]] = []
    checks: list[ReadinessCheck] = []
    for relative in REQUIRED_ARTIFACTS:
        path = root / relative
        exists = path.is_file()
        entry: dict[str, Any] = {
            "path": relative,
            "exists": exists,
            "size_bytes": path.stat().st_size if exists else 0,
            "sha256": _hash_bytes(path.read_bytes()) if exists else None,
        }
        inventory.append(entry)
        checks.append(
            ReadinessCheck(
                check_id=f"artifact.{relative.replace('/', '.')}",
                domain="artifact_integrity",
                status="PASS" if exists else "FAIL",
                severity="INFO" if exists else "CRITICAL",
                summary="Required release artifact is present" if exists else "Required release artifact is missing",
                details=entry,
            )
        )
    return inventory, checks


def _quality_checks(evidence: Mapping[str, Any]) -> list[ReadinessCheck]:
    decision = evidence.get("decision", {})
    regime = evidence.get("market_regime", {})
    risk_lab = evidence.get("risk_lab", {})
    governance = evidence.get("governance", {})
    provenance = evidence.get("data_provenance", {})
    checks: list[ReadinessCheck] = []

    row_sums = regime.get("transition_matrix_row_sums", {})
    transition_ok = bool(regime.get("transition_matrix_valid")) and all(abs(float(v) - 1.0) <= 1e-9 for v in row_sums.values())
    checks.append(ReadinessCheck(
        "data_quality.transition_matrix", "data_quality", "PASS" if transition_ok else "FAIL",
        "INFO" if transition_ok else "CRITICAL", "Regime transition rows sum to one", {"row_sums": row_sums},
    ))

    probabilities = decision.get("regime_probabilities", {})
    probability_total = sum(float(v) for v in probabilities.values()) if probabilities else 0.0
    probabilities_ok = bool(probabilities) and all(float(v) >= 0.0 for v in probabilities.values()) and abs(probability_total - 1.0) <= 1e-9
    checks.append(ReadinessCheck(
        "data_quality.regime_probabilities", "data_quality", "PASS" if probabilities_ok else "FAIL",
        "INFO" if probabilities_ok else "CRITICAL", "Decision probabilities are finite, nonnegative, and normalized",
        {"probabilities": probabilities, "sum": probability_total},
    ))

    weights = decision.get("target_weights", {})
    weight_total = sum(float(v) for v in weights.values()) if weights else 0.0
    feasibility = decision.get("feasibility", {})
    weights_ok = bool(weights) and abs(weight_total - 1.0) <= 1e-9 and feasibility.get("status") == "FEASIBLE"
    checks.append(ReadinessCheck(
        "data_quality.portfolio_feasibility", "data_quality", "PASS" if weights_ok else "FAIL",
        "INFO" if weights_ok else "CRITICAL", "Target portfolio is feasible and fully invested",
        {"weight_sum": weight_total, "feasibility": feasibility},
    ))

    scenarios = risk_lab.get("scenarios", [])
    scenario_ok = bool(scenarios) and all("scenario_id" in row and "evidence_class" in row for row in scenarios)
    checks.append(ReadinessCheck(
        "data_quality.scenario_lineage", "data_quality", "PASS" if scenario_ok else "FAIL",
        "INFO" if scenario_ok else "CRITICAL", "Risk scenarios carry stable identifiers and evidence classes",
        {"scenario_count": len(scenarios), "evidence_classes": sorted({row.get("evidence_class") for row in scenarios})},
    ))

    cvar_ok = risk_lab.get("cvar_convention", "").startswith("signed loss") and "cvar_loss_signed" in risk_lab and "downside_loss_magnitude" in risk_lab
    checks.append(ReadinessCheck(
        "control.cvar_display_discipline", "model_control", "PASS" if cvar_ok else "FAIL",
        "INFO" if cvar_ok else "CRITICAL", "Signed CVaR and nonnegative downside magnitude are both explicit",
        {"convention": risk_lab.get("cvar_convention"), "signed_loss": risk_lab.get("cvar_loss_signed"), "downside_magnitude": risk_lab.get("downside_loss_magnitude")},
    ))

    separation_ok = (
        governance.get("optimization_authorization") in {"AUTHORIZED", "BLOCKED"}
        and governance.get("research_promotion") == "RESEARCH_ONLY"
        and governance.get("human_review_required") is True
        and governance.get("execution_enabled") is False
    )
    checks.append(ReadinessCheck(
        "governance.authorization_promotion_separation", "governance", "PASS" if separation_ok else "FAIL",
        "INFO" if separation_ok else "CRITICAL", "Optimization authorization is separate from research promotion",
        {"optimization_authorization": governance.get("optimization_authorization"), "research_promotion": governance.get("research_promotion"), "human_review_required": governance.get("human_review_required"), "execution_enabled": governance.get("execution_enabled")},
    ))

    source_artifacts = provenance.get("source_artifacts", [])
    fallback_policy = str(provenance.get("missing_data_policy", ""))
    provenance_ok = bool(source_artifacts) and "fail explicitly" in fallback_policy.lower() and "silent" in fallback_policy.lower()
    checks.append(ReadinessCheck(
        "provenance.no_silent_fallback", "provenance", "PASS" if provenance_ok else "FAIL",
        "INFO" if provenance_ok else "HIGH", "Source artifacts and explicit missing-data behavior are declared",
        {"source_artifacts": source_artifacts, "missing_data_policy": fallback_policy},
    ))
    return checks


def build_role_policy() -> dict[str, Any]:
    """Return a declarative policy contract; enforcement belongs to deployment IAM."""
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_type": "DECLARATIVE_ROLE_CAPABILITY_CONTRACT",
        "enforcement_note": "This repository payload is descriptive. Production IAM, SSO, and approval enforcement must be supplied by the deployment boundary.",
        "roles": {
            "researcher": {"allow": ["read_evidence", "run_counterfactuals", "export_evidence"], "deny": ["promote_research", "enable_execution"]},
            "risk_officer": {"allow": ["read_evidence", "run_counterfactuals", "review_gates", "export_evidence"], "deny": ["enable_execution"]},
            "approver": {"allow": ["read_evidence", "review_gates", "record_human_review"], "deny": ["enable_execution_without_deployment_controls"]},
            "administrator": {"allow": ["manage_runtime_configuration", "manage_deployment_integrations"], "deny": ["change_model_claims_without_review", "enable_execution_in_research_build"]},
        },
        "required_controls": ["human_review", "immutable_evidence_export", "separate_promotion_workflow", "deployment_owned_authentication"],
    }


def build_audit_lineage(root: Path, evidence: Mapping[str, Any], inventory: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Build a reproducible hash-linked lineage summary without persisting state."""
    inventory = inventory or _artifact_inventory(root)[0]
    decision = evidence.get("decision", {})
    nodes = [
        {"node_id": "input.reference_fixture", "node_type": "data_input", "evidence_class": "BUNDLED_REFERENCE_DATA", "content_hash": _hash_json({"assets": decision.get("assets"), "regime_probabilities": decision.get("regime_probabilities")})},
        {"node_id": "model.mars_cvar", "node_type": "solver_output", "algorithm": decision.get("algorithm"), "decision_id": decision.get("decision_id"), "content_hash": _hash_json({"target_weights": decision.get("target_weights"), "objective": decision.get("objective"), "solver": decision.get("solver")})},
        {"node_id": "evidence.product_payload", "node_type": "evidence_bundle", "content_hash": _hash_json(evidence)},
        {"node_id": "artifact.release_manifest", "node_type": "release_artifact", "content_hash": next((x.get("sha256") for x in inventory if x.get("path") == "artifacts/mars_cvar/release_manifest.json"), None)},
    ]
    previous = "GENESIS"
    for node in nodes:
        node["previous_hash"] = previous
        node["lineage_hash"] = _hash_json({key: value for key, value in node.items() if key != "lineage_hash"})
        previous = node["lineage_hash"]
    return {
        "schema_version": READINESS_SCHEMA_VERSION,
        "hash_algorithm": "SHA-256",
        "root_hash": previous,
        "nodes": nodes,
        "immutability_note": "Hashes make exported evidence tamper-evident; storage immutability and access control remain deployment responsibilities.",
    }


def build_enterprise_readiness(root: Path, evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the enterprise control-plane payload for the current build."""
    if evidence is None:
        from src.institutional.mars_cvar_product import build_reference_product_evidence
        evidence = build_reference_product_evidence(root)
    inventory, artifact_checks = _artifact_inventory(root)
    quality_checks = _quality_checks(evidence)
    checks = artifact_checks + quality_checks
    failures = [check for check in checks if check.status == "FAIL"]
    overall = "READY_FOR_HUMAN_REVIEW" if not failures else "NOT_READY"
    lineage = build_audit_lineage(root, evidence, inventory)
    return {
        "schema_version": READINESS_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "service": "AURUM MARS-CVaR research workstation",
        "build_mode": "OFFLINE_FIRST_RESEARCH",
        "overall_status": overall,
        "release_gate": "PASS" if not failures else "FAIL",
        "decision_id": evidence.get("decision", {}).get("decision_id"),
        "scenario_count": evidence.get("risk_lab", {}).get("scenario_count", evidence.get("decision", {}).get("scenario_count")),
        "optimization_authorization": evidence.get("governance", {}).get("optimization_authorization"),
        "research_promotion": evidence.get("governance", {}).get("research_promotion"),
        "execution_enabled": evidence.get("governance", {}).get("execution_enabled"),
        "checks": [check.as_dict() for check in checks],
        "summary": {"total_checks": len(checks), "passed_checks": len(checks) - len(failures), "failed_checks": len(failures), "critical_failures": sum(check.severity == "CRITICAL" for check in failures)},
        "artifact_inventory": inventory,
        "audit_lineage": lineage,
        "role_policy": build_role_policy(),
        "operational_notes": [
            "No broker, order, or autonomous execution capability is enabled in this build.",
            "Production deployments should bind this contract to SSO/RBAC, immutable storage, alerting, and change management.",
            "A PASS means the evidence package is internally coherent and ready for human review; it is not investment approval.",
        ],
    }


def build_observability_snapshot(root: Path, readiness: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return low-cardinality health metrics safe for an operations endpoint."""
    readiness = readiness or build_enterprise_readiness(root)
    summary = readiness.get("summary", {})
    return {
        "schema_version": READINESS_SCHEMA_VERSION,
        "service": "AURUM MARS-CVaR research workstation",
        "status": "healthy" if readiness.get("release_gate") == "PASS" else "degraded",
        "metrics": {
            "readiness_release_gate": readiness.get("release_gate"),
            "readiness_checks_total": summary.get("total_checks", 0),
            "readiness_checks_failed": summary.get("failed_checks", 0),
            "evidence_scenario_count": readiness.get("scenario_count"),
            "execution_enabled": bool(readiness.get("execution_enabled", False)),
        },
        "decision_id": readiness.get("decision_id"),
        "research_promotion": readiness.get("research_promotion"),
        "no_secrets": True,
    }


def build_evidence_bundle(
    root: Path,
    evidence: Mapping[str, Any] | None = None,
    readiness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a portable, tamper-evident evidence record for enterprise storage."""
    if evidence is None:
        from src.institutional.mars_cvar_product import build_reference_product_evidence
        evidence = build_reference_product_evidence(root)
    readiness = readiness or build_enterprise_readiness(root, evidence)
    decision_id = evidence.get("decision", {}).get("decision_id")
    lineage = readiness.get("audit_lineage", {})
    base = {
        "schema_version": "1.0",
        "bundle_type": "AURUM_ENTERPRISE_EVIDENCE_BUNDLE",
        "generated_at_utc": _utc_now(),
        "run_id": f"{decision_id}:{str(lineage.get('root_hash', 'UNAVAILABLE'))[:16]}",
        "decision_id": decision_id,
        "algorithm": evidence.get("algorithm"),
        "bundle_evidence_hash": _hash_json(evidence),
        "lineage_root_hash": lineage.get("root_hash"),
        "governance": evidence.get("governance", {}),
        "provenance": evidence.get("data_provenance", {}),
        "readiness": {
            "overall_status": readiness.get("overall_status"),
            "release_gate": readiness.get("release_gate"),
            "summary": readiness.get("summary", {}),
        },
        "retention_policy": {
            "record_class": "INTERNAL_RESEARCH_EVIDENCE",
            "retention_period": "ORGANIZATION_DEFINED",
            "retention_owner_role": "risk_officer",
            "immutable_storage_required": True,
            "access_logging_required": True,
            "destruction_requires_approval": True,
            "legal_hold_supported_by_deployment": True,
        },
        "evidence": dict(evidence),
        "claim_boundary": evidence.get("claim_boundary"),
    }
    return {**base, "bundle_sha256": _hash_json(base)}
