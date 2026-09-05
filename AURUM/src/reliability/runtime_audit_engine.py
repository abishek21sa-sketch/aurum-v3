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


class RuntimeAuditEngine:
    def run(self, platform_report: dict, service_report: dict, alerts_report: dict) -> dict:
        findings = []

        for report in [platform_report, service_report]:
            for check in report.get("checks", []):
                if check["status"] != "healthy":
                    findings.append({
                        "service": check["service"],
                        "status": check["status"],
                        "detail": check["detail"],
                    })

        if alerts_report["alert_count"] > 0:
            readiness = "review_required"
        else:
            readiness = "ready"

        audit = {
            "timestamp": utc_now(),
            "layer": "runtime_audit",
            "readiness": readiness,
            "finding_count": len(findings),
            "findings": findings,
        }

        save_json(RESULTS_DIR / "runtime_audit_report.json", audit)
        return audit