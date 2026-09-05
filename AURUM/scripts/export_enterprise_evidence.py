"""Export the AURUM evidence bundle for immutable enterprise storage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.institutional.enterprise_readiness import build_evidence_bundle


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/product_runtime/enterprise_evidence_bundle.json"


def export_bundle(output: Path = DEFAULT_OUTPUT) -> dict:
    bundle = build_evidence_bundle(ROOT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    bundle = export_bundle(args.output)
    print("AURUM_EVIDENCE_BUNDLE_STATUS=PASS")
    print(f"AURUM_EVIDENCE_BUNDLE_RUN_ID={bundle['run_id']}")
    print(f"AURUM_EVIDENCE_BUNDLE_SHA256={bundle['bundle_sha256']}")
    print(f"AURUM_EVIDENCE_BUNDLE_PATH={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
