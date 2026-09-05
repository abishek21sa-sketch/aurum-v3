from pathlib import Path
from datetime import datetime, timezone
import json


RESULTS_DIR = Path("results/reliability")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class PlatformHealthMonitor:
    def check_results_dir(self) -> dict:
        exists = Path("results").exists()
        return {
            "service": "results_directory",
            "status": "healthy" if exists else "unhealthy",
            "detail": "results directory exists" if exists else "results directory missing",
        }

    def check_src_dir(self) -> dict:
        exists = Path("src").exists()
        return {
            "service": "src_directory",
            "status": "healthy" if exists else "unhealthy",
            "detail": "src directory exists" if exists else "src directory missing",
        }

    def run(self) -> dict:
        checks = [
            self.check_results_dir(),
            self.check_src_dir(),
        ]

        healthy = all(c["status"] == "healthy" for c in checks)

        report = {
            "timestamp": utc_now(),
            "layer": "platform_health",
            "status": "healthy" if healthy else "degraded",
            "checks": checks,
        }

        save_json(RESULTS_DIR / "platform_health_report.json", report)
        return report