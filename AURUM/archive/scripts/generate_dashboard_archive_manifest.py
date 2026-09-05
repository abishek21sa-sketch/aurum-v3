from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

from src.config.storage_paths import SPRINT_RESULTS_DIR, ensure_storage_dirs
from src.platform.dashboard_registry import DashboardRegistry


@dataclass
class DashboardArchiveItem:
    path: str
    filename: str
    recommendation: str


@dataclass
class DashboardArchiveManifest:
    official_dashboard: str
    archive_count: int
    archive_candidates: List[DashboardArchiveItem]
    status: str


def generate_manifest() -> DashboardArchiveManifest:
    result = DashboardRegistry().scan()

    archive_items = [
        DashboardArchiveItem(
            path=path,
            filename=Path(path).name,
            recommendation="archive_candidate_do_not_launch_directly",
        )
        for path in result.archived_candidates
    ]

    manifest = DashboardArchiveManifest(
        official_dashboard=result.official_dashboard,
        archive_count=len(archive_items),
        archive_candidates=archive_items,
        status="dashboard_archive_manifest_created",
    )

    ensure_storage_dirs()
    output = SPRINT_RESULTS_DIR / "dashboard_archive_manifest.json"
    output.write_text(
        json.dumps(
            {
                "official_dashboard": manifest.official_dashboard,
                "archive_count": manifest.archive_count,
                "archive_candidates": [asdict(item) for item in archive_items],
                "status": manifest.status,
            },
            indent=4,
        ),
        encoding="utf-8",
    )

    return manifest


def main() -> None:
    manifest = generate_manifest()

    print("=" * 80)
    print("AURUM DASHBOARD ARCHIVE MANIFEST")
    print("=" * 80)
    print(f"Official Dashboard: {manifest.official_dashboard}")
    print(f"Archive Candidates: {manifest.archive_count}")
    print(f"Status:             {manifest.status}")
    print("-" * 80)

    for item in manifest.archive_candidates:
        print(f"[ARCHIVE CANDIDATE] {item.path}")

    print("=" * 80)


if __name__ == "__main__":
    main()