from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

from src.config.storage_paths import SPRINT_RESULTS_DIR, ensure_storage_dirs


SEARCH_ROOTS = [
    Path("src"),
    Path("scripts"),
]

PATTERNS = [
    'Path("results',
    "Path('results",
    '"results/',
    "'results/",
    '"results\\',
    "'results\\",
]


@dataclass
class HardcodedPathFinding:
    file: str
    line_number: int
    line: str
    pattern: str


@dataclass
class HardcodedPathAuditResult:
    finding_count: int
    findings: List[HardcodedPathFinding]
    status: str


def audit() -> HardcodedPathAuditResult:
    findings: List[HardcodedPathFinding] = []

    for root in SEARCH_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*.py"):
            if path.name == "storage_paths.py":
                continue

            text = path.read_text(encoding="utf-8", errors="ignore").splitlines()

            for idx, line in enumerate(text, start=1):
                for pattern in PATTERNS:
                    if pattern in line:
                        findings.append(
                            HardcodedPathFinding(
                                file=str(path),
                                line_number=idx,
                                line=line.strip(),
                                pattern=pattern,
                            )
                        )

    status = "clean" if not findings else "hardcoded_paths_found"

    result = HardcodedPathAuditResult(
        finding_count=len(findings),
        findings=findings,
        status=status,
    )

    ensure_storage_dirs()
    output = SPRINT_RESULTS_DIR / "hardcoded_path_audit.json"
    output.write_text(
        json.dumps(
            {
                "finding_count": result.finding_count,
                "status": result.status,
                "findings": [asdict(f) for f in result.findings],
            },
            indent=4,
        ),
        encoding="utf-8",
    )

    return result


def main() -> None:
    result = audit()

    print("=" * 80)
    print("AURUM HARDCODED PATH AUDIT")
    print("=" * 80)
    print(f"Findings: {result.finding_count}")
    print(f"Status:   {result.status}")
    print("-" * 80)

    for finding in result.findings[:50]:
        print(f"{finding.file}:{finding.line_number}")
        print(f"  {finding.line}")

    if result.finding_count > 50:
        print(f"... {result.finding_count - 50} more findings omitted")

    print("=" * 80)


if __name__ == "__main__":
    main()