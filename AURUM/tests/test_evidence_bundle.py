import json
from pathlib import Path

from src.institutional.enterprise_readiness import build_evidence_bundle
from src.institutional.mars_cvar_product import build_reference_product_evidence


ROOT = Path(__file__).resolve().parents[1]


def test_evidence_bundle_has_stable_identity_and_storage_controls():
    evidence = build_reference_product_evidence(ROOT)
    bundle = build_evidence_bundle(ROOT, evidence)
    assert bundle["bundle_type"] == "AURUM_ENTERPRISE_EVIDENCE_BUNDLE"
    assert bundle["run_id"].startswith("MARS-812FA013EB90FFA1:")
    assert bundle["decision_id"] == "MARS-812FA013EB90FFA1"
    assert bundle["governance"]["execution_enabled"] is False
    assert bundle["retention_policy"]["immutable_storage_required"] is True
    assert len(bundle["bundle_sha256"]) == 64


def test_evidence_bundle_is_json_serializable_and_claim_bounded():
    bundle = build_evidence_bundle(ROOT)
    serialized = json.dumps(bundle, sort_keys=True)
    assert "AURUM_ENTERPRISE_EVIDENCE_BUNDLE" in serialized
    assert "production promotion" in bundle["claim_boundary"]
