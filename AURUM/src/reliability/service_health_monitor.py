from pathlib import Path
from datetime import datetime, timezone
import json

from src.database.postgres_manager import PostgresManager
from src.market_data.market_data_service import MarketDataService


RESULTS_DIR = Path("results/reliability")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class ServiceHealthMonitor:
    def check_postgres(self) -> dict:
        try:
            db = PostgresManager()
            row = db.fetch_one("SELECT 1 AS ok;")
            ok = row and row["ok"] == 1
            return {
                "service": "postgres",
                "status": "healthy" if ok else "unhealthy",
                "detail": "Postgres connection OK",
            }
        except Exception as exc:
            return {
                "service": "postgres",
                "status": "unhealthy",
                "detail": str(exc),
            }

    def check_market_data(self) -> dict:
        try:
            market = MarketDataService()
            provider = market.provider_name()
            history = market.get_history("SPY", period="5d")
            ok = history is not None and not history.empty

            return {
                "service": "market_data",
                "status": "healthy" if ok else "unhealthy",
                "detail": f"provider={provider}",
            }
        except Exception as exc:
            return {
                "service": "market_data",
                "status": "unhealthy",
                "detail": str(exc),
            }

    def check_portfolio_os_artifacts(self) -> dict:
        required = [
            Path("results/portfolio_os/portfolio_operating_system.json"),
            Path("results/portfolio_os/portfolio_directive.json"),
        ]

        missing = [str(p) for p in required if not p.exists()]

        return {
            "service": "portfolio_os",
            "status": "healthy" if not missing else "degraded",
            "detail": "all core artifacts exist" if not missing else f"missing={missing}",
        }

    def check_committee_artifacts(self) -> dict:
        candidates = [
            Path("results/research/committee_decision.json"),
            Path("results/research/investment_committee_minutes.json"),
            Path("results/governance/investment_committee_decision.json"),
        ]

        ok = any(p.exists() for p in candidates)

        return {
            "service": "committee",
            "status": "healthy" if ok else "degraded",
            "detail": "committee artifact found" if ok else "committee artifact missing",
        }

    def check_dashboard(self) -> dict:
        candidates = [
            Path("dashboard/official_dashboard.py"),
            Path("src/dashboard/institutional_command_center.py"),
        ]

        found = [str(path) for path in candidates if path.exists()]

        return {
            "service": "dashboard",
            "status": "healthy" if found else "unhealthy",
            "detail": "official dashboard found: " + ", ".join(found)
            if found
            else "official dashboard missing",
        }

    def run(self) -> dict:
        checks = [
            self.check_postgres(),
            self.check_market_data(),
            self.check_portfolio_os_artifacts(),
            self.check_committee_artifacts(),
            self.check_dashboard(),
        ]

        unhealthy = [c for c in checks if c["status"] == "unhealthy"]
        degraded = [c for c in checks if c["status"] == "degraded"]

        if unhealthy:
            status = "unhealthy"
        elif degraded:
            status = "degraded"
        else:
            status = "healthy"

        report = {
            "timestamp": utc_now(),
            "layer": "service_health",
            "status": status,
            "checks": checks,
        }

        save_json(RESULTS_DIR / "service_health_report.json", report)
        return report