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


class AlertEngine:
    def generate_alerts(self, reports: list[dict]) -> dict:
        alerts = []

        for report in reports:
            for check in report.get("checks", []):
                if check["status"] == "unhealthy":
                    alerts.append({
                        "severity": "critical",
                        "service": check["service"],
                        "message": check["detail"],
                    })
                elif check["status"] == "degraded":
                    alerts.append({
                        "severity": "warning",
                        "service": check["service"],
                        "message": check["detail"],
                    })

        status = "clear" if not alerts else "active"

        result = {
            "timestamp": utc_now(),
            "alert_status": status,
            "alert_count": len(alerts),
            "alerts": alerts,
        }

        save_json(RESULTS_DIR / "alerts_report.json", result)
        return result