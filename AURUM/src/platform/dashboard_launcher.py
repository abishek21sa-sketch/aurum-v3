from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

from src.config.storage_paths import SPRINT_RESULTS_DIR, ensure_storage_dirs
from src.platform.dashboard_registry import DashboardRegistry


@dataclass
class DashboardLaunchPlan:
    official_dashboard: str
    official_dashboard_path: Optional[str]
    archive_candidates: List[str]
    launch_command: List[str]
    status: str


class DashboardLauncher:
    """
    Single official dashboard entrypoint for AURUM.

    This does not delete or move old dashboards.
    It declares and launches the official dashboard only.
    """

    def __init__(self) -> None:
        self.registry = DashboardRegistry()

    def build_launch_plan(self) -> DashboardLaunchPlan:
        registry_result = self.registry.scan()

        official_path = self._find_official_dashboard(
            registry_result.official_dashboard
        )

        status = (
            "official_dashboard_ready"
            if official_path is not None
            else "official_dashboard_missing"
        )

        launch_command = (
            ["streamlit", "run", official_path]
            if official_path is not None
            else []
        )

        plan = DashboardLaunchPlan(
            official_dashboard=registry_result.official_dashboard,
            official_dashboard_path=official_path,
            archive_candidates=registry_result.archived_candidates,
            launch_command=launch_command,
            status=status,
        )

        ensure_storage_dirs()
        output = SPRINT_RESULTS_DIR / "dashboard_launch_plan.json"
        output.write_text(json.dumps(asdict(plan), indent=4), encoding="utf-8")

        return plan

    @staticmethod
    def _find_official_dashboard(filename: str) -> Optional[str]:
        search_roots = [Path("src"), Path("dashboards"), Path("streamlit")]

        for root in search_roots:
            if not root.exists():
                continue

            for file in root.rglob(filename):
                return str(file)

        return None

    def launch(self) -> None:
        plan = self.build_launch_plan()

        if not plan.official_dashboard_path:
            raise FileNotFoundError(
                f"Official dashboard not found: {plan.official_dashboard}"
            )

        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", plan.official_dashboard_path],
            check=True,
        )


def main() -> None:
    launcher = DashboardLauncher()
    plan = launcher.build_launch_plan()

    print("=" * 80)
    print("AURUM DASHBOARD LAUNCHER")
    print("=" * 80)
    print(f"Official Dashboard: {plan.official_dashboard}")
    print(f"Dashboard Path:     {plan.official_dashboard_path}")
    print(f"Archive Candidates: {len(plan.archive_candidates)}")
    print(f"Status:             {plan.status}")
    print("-" * 80)

    if plan.launch_command:
        print("Launch command:")
        print(" ".join(plan.launch_command))
    else:
        print("Launch command unavailable because official dashboard was not found.")

    print("=" * 80)


if __name__ == "__main__":
    main()