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


class InstitutionalReadinessScore:
    def calculate(self, platform_report: dict, service_report: dict, alerts_report: dict, audit_report: dict) -> dict:
        score = 100

        for report in [platform_report, service_report]:
            for check in report.get("checks", []):
                if check["status"] == "unhealthy":
                    score -= 20
                elif check["status"] == "degraded":
                    score -= 8

        score -= min(alerts_report.get("alert_count", 0) * 5, 25)
        score -= min(audit_report.get("finding_count", 0) * 3, 15)

        score = max(score, 0)

        if score >= 90:
            status = "institutional_ready"
        elif score >= 75:
            status = "conditionally_ready"
        elif score >= 60:
            status = "degraded"
        else:
            status = "not_ready"

        result = {
            "timestamp": utc_now(),
            "institutional_readiness_score": score,
            "status": status,
            "summary": {
                "platform_status": platform_report["status"],
                "service_status": service_report["status"],
                "alert_status": alerts_report["alert_status"],
                "runtime_readiness": audit_report["readiness"],
            },
        }

        save_json(RESULTS_DIR / "institutional_readiness_score.json", result)
        return result