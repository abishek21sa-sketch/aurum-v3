from pathlib import Path

from scripts.verify_enterprise_release import verify_release_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_release_verifier_passes_hashes_hygiene_and_readiness():
    result = verify_release_manifest(ROOT)
    assert result["status"] == "PASS"
    assert result["summary"]["failed_checks"] == 0
    assert result["release_fingerprint"]
    assert result["promotion_state"] == "RESEARCH_ONLY"
    assert result["execution_enabled"] is False


def test_release_verifier_detects_tampered_file(tmp_path):
    manifest = tmp_path / "release_manifest.json"
    manifest.write_text('{"algorithm":"MARS-CVaR","files":{"missing.txt":{"sha256":"bad","bytes":3}}}', encoding="utf-8")
    result = verify_release_manifest(ROOT, manifest)
    assert result["status"] == "FAIL"
    assert any(check["check_id"] == "manifest.file_hashes" and check["status"] == "FAIL" for check in result["checks"])
