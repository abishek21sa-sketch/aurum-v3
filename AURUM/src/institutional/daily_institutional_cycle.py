from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List
import json

from src.portfolio_os.portfolio_operating_system import main as run_portfolio_os
from src.research_firm.ai_research_firm_mode import AIResearchFirmMode
from src.portfolio_os.research_firm_bridge import ResearchFirmPortfolioOSBridge
from src.cio.chief_investment_officer_agent import ChiefInvestmentOfficerAgent
from src.database.postgres_manager import PostgresManager
from src.database.repositories.intelligence_repository import IntelligenceRepository
from src.reliability.platform_health_monitor import PlatformHealthMonitor
from src.reliability.service_health_monitor import ServiceHealthMonitor
from src.reliability.alert_engine import AlertEngine
from src.reliability.runtime_audit_engine import RuntimeAuditEngine
from src.reliability.institutional_readiness_score import InstitutionalReadinessScore


RESULTS_DIR = Path("results/institutional")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path, default: Any = None) -> Any:
    if default is None:
        default = {}

    path = Path(path)

    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


class DailyInstitutionalCycle:
    def run(self) -> Dict:
        stages: List[Dict] = []

        try:
            run_portfolio_os()
            stages.append(self.stage("portfolio_os", "complete"))
        except Exception as exc:
            stages.append(self.stage("portfolio_os", "failed", str(exc)))

        try:
            research_firm = AIResearchFirmMode().run()
            stages.append(self.stage("ai_research_firm", "complete", self.compact(research_firm)))
        except Exception as exc:
            research_firm = {}
            stages.append(self.stage("ai_research_firm", "failed", str(exc)))

        try:
            bridge = ResearchFirmPortfolioOSBridge().build_bridge()
            stages.append(self.stage("research_firm_portfolio_os_bridge", "complete", bridge))
        except Exception as exc:
            bridge = {}
            stages.append(self.stage("research_firm_portfolio_os_bridge", "failed", str(exc)))

        try:
            cio = ChiefInvestmentOfficerAgent().run()
            stages.append(self.stage("cio", "complete", cio.get("portfolio_directive", {})))
        except Exception as exc:
            cio = {}
            stages.append(self.stage("cio", "failed", str(exc)))

        try:
            persistence = self.persist_intelligence()
            stages.append(self.stage("intelligence_persistence", "complete", persistence))
        except Exception as exc:
            persistence = {}
            stages.append(self.stage("intelligence_persistence", "failed", str(exc)))

        try:
            reliability = self.run_reliability()
            stages.append(self.stage("reliability", "complete", reliability))
        except Exception as exc:
            reliability = {}
            stages.append(self.stage("reliability", "failed", str(exc)))

        status = "complete" if all(stage["status"] == "complete" for stage in stages) else "degraded"

        cycle = {
            "timestamp": utc_now(),
            "cycle": "aurum_daily_institutional_cycle",
            "status": status,
            "stage_count": len(stages),
            "stages": stages,
            "executive_summary": self.executive_summary(
                research_firm=research_firm,
                bridge=bridge,
                cio=cio,
                reliability=reliability,
            ),
        }

        (RESULTS_DIR / "daily_institutional_cycle.json").write_text(
            json.dumps(cycle, indent=2),
            encoding="utf-8",
        )

        return cycle

    def stage(self, name: str, status: str, output: Any = None) -> Dict:
        return {
            "stage": name,
            "status": status,
            "timestamp": utc_now(),
            "output_summary": output if output is not None else {},
        }

    def compact(self, payload: Dict) -> Dict:
        summary = payload.get("executive_summary", {})
        return {
            "status": payload.get("status"),
            "stage_count": payload.get("stage_count"),
            "best_alpha": summary.get("best_alpha"),
            "worst_scenario": summary.get("worst_portfolio_scenario"),
            "cio_action": summary.get("cio_recommended_action"),
        }

    def persist_intelligence(self) -> Dict:
        db = PostgresManager()
        repo = IntelligenceRepository(db)
        repo.initialize_tables()

        cio_directive = load_json("results/cio/cio_portfolio_directive.json")
        research_firm = load_json("results/research_firm/ai_research_firm_mode.json")
        alpha_rankings = load_json("results/alpha_ranking/institutional_research_rankings.json")
        portfolio_lab = load_json("results/portfolio_lab_2/portfolio_lab_results.json")

        repo.insert_cio_directive(cio_directive)
        repo.insert_research_firm_run(research_firm)
        alpha_inserted = repo.insert_alpha_rankings(alpha_rankings)
        scenarios_inserted = repo.insert_portfolio_lab_scenarios(portfolio_lab)

        return {
            "cio_directive_inserted": True,
            "research_firm_run_inserted": True,
            "alpha_rankings_inserted": alpha_inserted,
            "portfolio_lab_scenarios_inserted": scenarios_inserted,
        }

    def run_reliability(self) -> Dict:
        platform = PlatformHealthMonitor().run()
        service = ServiceHealthMonitor().run()
        alerts = AlertEngine().generate_alerts([platform, service])
        audit = RuntimeAuditEngine().run(platform, service, alerts)
        readiness = InstitutionalReadinessScore().calculate(platform, service, alerts, audit)

        return {
            "platform_status": platform.get("status"),
            "service_status": service.get("status"),
            "alert_count": alerts.get("alert_count"),
            "runtime_readiness": audit.get("readiness"),
            "institutional_readiness_score": readiness.get("institutional_readiness_score"),
            "status": readiness.get("status"),
        }

    def executive_summary(
        self,
        research_firm: Dict,
        bridge: Dict,
        cio: Dict,
        reliability: Dict,
    ) -> Dict:
        research_summary = research_firm.get("executive_summary", {})
        cio_directive = cio.get("portfolio_directive", {})

        return {
            "firm_view": research_summary.get("firm_view", "unknown"),
            "best_alpha": bridge.get("top_alpha", research_summary.get("best_alpha", "unknown")),
            "primary_risk": bridge.get("primary_risk", research_summary.get("worst_portfolio_scenario", "unknown")),
            "cio_action": cio_directive.get("recommended_action", bridge.get("cio_recommended_action", "unknown")),
            "cio_risk_posture": cio_directive.get("risk_posture", bridge.get("cio_risk_posture", "unknown")),
            "execution_permission": cio_directive.get("execution_permission", bridge.get("cio_execution_permission", "unknown")),
            "readiness_score": reliability.get("institutional_readiness_score", 0),
            "interpretation": (
                "AURUM completed the daily institutional cycle by running Portfolio OS, "
                "AI Research Firm Mode, CIO synthesis, Portfolio OS bridge, intelligence persistence, "
                "and reliability monitoring."
            ),
        }


def main() -> None:
    cycle = DailyInstitutionalCycle().run()
    summary = cycle["executive_summary"]

    print("=" * 80)
    print("AURUM PHASE 6C.6 DAILY INSTITUTIONAL CYCLE")
    print("=" * 80)
    print(f"Status:               {cycle['status']}")
    print(f"Stages:               {cycle['stage_count']}")
    print(f"Firm View:            {summary['firm_view']}")
    print(f"Best Alpha:           {summary['best_alpha']}")
    print(f"Primary Risk:         {summary['primary_risk']}")
    print(f"CIO Action:           {summary['cio_action']}")
    print(f"CIO Risk Posture:     {summary['cio_risk_posture']}")
    print(f"Execution Permission: {summary['execution_permission']}")
    print(f"Readiness Score:      {summary['readiness_score']}")
    print("=" * 80)


if __name__ == "__main__":
    main()