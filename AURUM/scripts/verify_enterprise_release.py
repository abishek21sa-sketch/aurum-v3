"""Verify the AURUM release manifest and enterprise control contract.

This verifier is intentionally dependency-light so it can run in CI, a
release workstation, or a deployment image before the service starts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "artifacts/mars_cvar/release_manifest.json"
SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "__pycache__", ".pytest_cache"}
SECRET_FILE_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fingerprint(entries: dict[str, Any]) -> str:
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _check(check_id: str, status: str, summary: str, **details: Any) -> dict[str, Any]:
    return {"check_id": check_id, "status": status, "summary": summary, "details": details}


def _sensitive_paths(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        name = path.name.lower()
        if name in SECRET_FILE_NAMES or path.suffix.lower() in SECRET_SUFFIXES:
            findings.append(str(path.relative_to(root)).replace("\\", "/"))
    return sorted(findings)


def _schema_validation(root: Path, readiness: dict[str, Any]) -> dict[str, Any]:
    schema_paths = {
        "readiness": root / "schemas/aurum_readiness.schema.json",
        "role_policy": root / "schemas/aurum_role_policy.schema.json",
        "evidence_bundle": root / "schemas/aurum_evidence_bundle.schema.json",
        "sbom": root / "schemas/aurum_sbom.schema.json",
    }
    try:
        import jsonschema
    except ImportError as exc:
        return {"status": "FAIL", "error": f"jsonschema unavailable: {exc}", "errors": []}

    errors: list[dict[str, str]] = []
    for name, schema_path in schema_paths.items():
        if not schema_path.is_file():
            errors.append({"contract": name, "error": "schema missing"})
            continue
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
            if name == "readiness":
                instance = readiness
            elif name == "role_policy":
                instance = readiness.get("role_policy", {})
            elif name == "evidence_bundle":
                bundle_path = root / "artifacts/product_runtime/enterprise_evidence_bundle.json"
                if not bundle_path.is_file():
                    errors.append({"contract": name, "error": "evidence bundle export missing"})
                    continue
                instance = json.loads(bundle_path.read_text(encoding="utf-8"))
            else:
                sbom_path = root / "artifacts/compliance/sbom.json"
                if not sbom_path.is_file():
                    errors.append({"contract": name, "error": "SBOM export missing"})
                    continue
                instance = json.loads(sbom_path.read_text(encoding="utf-8"))
            for error in jsonschema.Draft202012Validator(schema).iter_errors(instance):
                errors.append({"contract": name, "path": ".".join(str(part) for part in error.path), "error": error.message})
        except (OSError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
            errors.append({"contract": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def verify_release_manifest(root: Path = ROOT, manifest_path: Path = MANIFEST) -> dict[str, Any]:
    """Verify hashes, release hygiene, and readiness without modifying files."""
    checks: list[dict[str, Any]] = []
    if not manifest_path.is_file():
        checks.append(_check("manifest.present", "FAIL", "Release manifest is missing", path=str(manifest_path)))
        return {"status": "FAIL", "manifest": str(manifest_path), "checks": checks, "release_fingerprint": None}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = manifest.get("files", {})
        valid_shape = isinstance(entries, dict) and bool(entries)
    except (OSError, json.JSONDecodeError) as exc:
        checks.append(_check("manifest.parseable", "FAIL", "Release manifest is not valid JSON", error=str(exc)))
        return {"status": "FAIL", "manifest": str(manifest_path), "checks": checks, "release_fingerprint": None}

    checks.append(_check("manifest.parseable", "PASS" if valid_shape else "FAIL", "Release manifest has a non-empty file inventory", file_count=len(entries)))
    mismatches: list[dict[str, Any]] = []
    for relative, expected in entries.items():
        path = root / relative
        if not path.is_file():
            mismatches.append({"path": relative, "reason": "missing"})
            continue
        actual_hash = _sha256(path)
        actual_bytes = path.stat().st_size
        if actual_hash != expected.get("sha256") or actual_bytes != expected.get("bytes"):
            mismatches.append({"path": relative, "reason": "hash_or_size_mismatch", "expected_sha256": expected.get("sha256"), "actual_sha256": actual_hash, "expected_bytes": expected.get("bytes"), "actual_bytes": actual_bytes})
    checks.append(_check("manifest.file_hashes", "PASS" if not mismatches else "FAIL", "Every release-manifest file matches its recorded SHA-256 and size", mismatches=mismatches, verified_count=len(entries) - len(mismatches)))

    sensitive = _sensitive_paths(root)
    checks.append(_check("release.secret_hygiene", "PASS" if not sensitive else "FAIL", "No private-key or environment-secret filenames are present", findings=sensitive))
    vcs = sorted({part for path in root.rglob("*") if path.is_dir() for part in path.relative_to(root).parts if part in {".git", ".hg", ".svn"}})
    checks.append(_check("release.vcs_hygiene", "PASS" if not vcs else "FAIL", "No VCS metadata is present in the distributable root", findings=vcs))

    from src.institutional.enterprise_readiness import build_enterprise_readiness

    readiness = build_enterprise_readiness(root)
    readiness_ok = readiness.get("release_gate") == "PASS"
    checks.append(_check("control_plane.readiness", "PASS" if readiness_ok else "FAIL", "Enterprise readiness contract passes", overall_status=readiness.get("overall_status"), readiness_summary=readiness.get("summary")))
    schema_result = _schema_validation(root, readiness)
    checks.append(_check("control_plane.schemas", schema_result["status"], "Readiness and role-policy payloads validate against versioned JSON Schemas", **{key: value for key, value in schema_result.items() if key != "status"}))

    failures = [check for check in checks if check["status"] == "FAIL"]
    return {
        "schema_version": "1.0",
        "status": "PASS" if not failures else "FAIL",
        "manifest": str(manifest_path.relative_to(root)).replace("\\", "/") if manifest_path.is_relative_to(root) else str(manifest_path),
        "algorithm": manifest.get("algorithm"),
        "release_fingerprint": _fingerprint(entries),
        "checks": checks,
        "summary": {"total_checks": len(checks), "passed_checks": len(checks) - len(failures), "failed_checks": len(failures)},
        "decision_id": readiness.get("decision_id"),
        "promotion_state": readiness.get("research_promotion"),
        "execution_enabled": readiness.get("execution_enabled"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the full machine-readable payload")
    args = parser.parse_args()
    result = verify_release_manifest()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"AURUM_RELEASE_MANIFEST_STATUS={result['status']}")
        print(f"AURUM_RELEASE_FINGERPRINT={result['release_fingerprint'] or 'UNAVAILABLE'}")
        print(f"AURUM_RELEASE_CHECKS={result['summary']['passed_checks']}/{result['summary']['total_checks']}")
        print(f"AURUM_PROMOTION_STATE={result.get('promotion_state')}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
