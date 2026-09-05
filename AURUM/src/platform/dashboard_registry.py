from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

from src.config.storage_paths import SPRINT_RESULTS_DIR, ensure_storage_dirs


@dataclass
class DashboardRegistryResult:
    official_dashboard: str
    archived_candidates: List[str]
    recommendation: str
    status: str


class DashboardRegistry:
    """
    Sprint 2 cleanup registry.

    This does not delete old dashboards.
    It declares one official dashboard and records the rest as archive candidates.
    """

    def __init__(self) -> None:
        self.official_dashboard = "institutional_command_center.py"

    def scan(self) -> DashboardRegistryResult:
        candidates = []

        search_roots = [
            Path("src/dashboard"),
            Path("src/dashboards"),
            Path("dashboards"),
            Path("streamlit"),
        ]

        excluded_files = {
            "dashboard_launcher.py",
            "dashboard_registry.py",
            "runtime_dashboard_data.py",
        }

        for root in search_roots:
            if not root.exists():
                continue

            for file in root.rglob("*.py"):
                name = file.name.lower()

                if name in excluded_files:
                    continue

                if "dashboard" in name or "command_center" in name:
                    candidates.append(str(file))

        archived = [
            path for path in candidates
            if Path(path).name != self.official_dashboard
        ]

        result = DashboardRegistryResult(
            official_dashboard=self.official_dashboard,
            archived_candidates=archived,
            recommendation=(
                "Use institutional_command_center.py as the single official dashboard. "
                "Keep other dashboards as archive candidates until manually reviewed."
            ),
            status="dashboard_registry_created",
        )

        ensure_storage_dirs()
        output = SPRINT_RESULTS_DIR / "dashboard_registry.json"
        output.write_text(json.dumps(asdict(result), indent=4), encoding="utf-8")

        return result

def main() -> None:
    result = DashboardRegistry().scan()

    print("=" * 80)
    print("AURUM DASHBOARD REGISTRY")
    print("=" * 80)
    print(f"Official Dashboard: {result.official_dashboard}")
    print(f"Archive Candidates: {len(result.archived_candidates)}")
    print(f"Status:             {result.status}")
    print("=" * 80)


if __name__ == "__main__":
    main()