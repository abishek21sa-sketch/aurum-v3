"""Generate a deterministic CycloneDX-style SBOM from pinned requirements."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import uuid


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
DEFAULT_OUTPUT = ROOT / "artifacts/compliance/sbom.json"
PINNED_REQUIREMENT = re.compile(r"^([A-Za-z0-9_.-]+)\s*==\s*([^\s;]+)")


def _requirements_components(path: Path) -> list[dict[str, str]]:
    components: list[dict[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith(("-r", "--")):
            continue
        match = PINNED_REQUIREMENT.match(line)
        if match is None:
            raise ValueError(f"Requirement is not pinned with ==: {raw_line}")
        name, version = match.groups()
        normalized = name.lower().replace("_", "-")
        components.append(
            {
                "type": "library",
                "group": "pypi",
                "name": name,
                "version": version,
                "purl": f"pkg:pypi/{normalized}@{version}",
            }
        )
    if not components:
        raise ValueError(f"No pinned components found in {path}")
    return sorted(components, key=lambda item: (item["name"].lower(), item["version"]))


def build_sbom(requirements: Path = REQUIREMENTS) -> dict:
    components = _requirements_components(requirements)
    source_hash = hashlib.sha256(requirements.read_bytes()).hexdigest()
    component_fingerprint = hashlib.sha256(json.dumps(components, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    serial = uuid.UUID(component_fingerprint[:32])
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{serial}",
        "version": 1,
        "metadata": {
            "component": {"type": "application", "group": "aurum", "name": "AURUM MARS-CVaR research workstation"},
            "properties": [{"name": "requirements.sha256", "value": source_hash}, {"name": "generation.mode", "value": "deterministic-offline"}],
        },
        "components": components,
    }


def export_sbom(output: Path = DEFAULT_OUTPUT) -> dict:
    sbom = build_sbom()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sbom


def main() -> int:
    sbom = export_sbom()
    print("AURUM_SBOM_STATUS=PASS")
    print(f"AURUM_SBOM_COMPONENTS={len(sbom['components'])}")
    print(f"AURUM_SBOM_SERIAL={sbom['serialNumber']}")
    print(f"AURUM_SBOM_PATH={DEFAULT_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
