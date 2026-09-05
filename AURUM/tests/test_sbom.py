import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.generate_sbom import build_sbom


ROOT = Path(__file__).resolve().parents[1]


def test_sbom_is_deterministic_and_fully_pinned():
    first = build_sbom()
    second = build_sbom()
    assert first == second
    assert len(first["components"]) >= 50
    assert len({item["name"].lower() for item in first["components"]}) == len(first["components"])
    assert all(item["version"] and item["purl"].startswith("pkg:pypi/") for item in first["components"])


def test_sbom_validates_against_versioned_schema():
    sbom = build_sbom()
    schema = json.loads((ROOT / "schemas/aurum_sbom.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert list(Draft202012Validator(schema).iter_errors(sbom)) == []
