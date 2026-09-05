from src.reliability.platform_health_monitor import PlatformHealthMonitor
from src.reliability.service_health_monitor import ServiceHealthMonitor
from src.reliability.alert_engine import AlertEngine
from src.reliability.runtime_audit_engine import RuntimeAuditEngine
from src.reliability.institutional_readiness_score import InstitutionalReadinessScore


def check(condition: bool, label: str, detail: str = ""):
    if condition:
        print(f"[PASS] {label}")
        if detail:
            print(f"       {detail}")
    else:
        print(f"[FAIL] {label}")
        if detail:
            print(f"       {detail}")
        raise SystemExit(1)


def main():
    print("=" * 80)
    print("AURUM PHASE 6A.5 RELIABILITY LAYER VALIDATION")
    print("=" * 80)

    platform = PlatformHealthMonitor().run()
    service = ServiceHealthMonitor().run()
    alerts = AlertEngine().generate_alerts([platform, service])
    audit = RuntimeAuditEngine().run(platform, service, alerts)
    readiness = InstitutionalReadinessScore().calculate(platform, service, alerts, audit)

    check(platform["status"] == "healthy", "Platform health monitor", platform["status"])

    postgres = next(c for c in service["checks"] if c["service"] == "postgres")
    market = next(c for c in service["checks"] if c["service"] == "market_data")
    dashboard = next(c for c in service["checks"] if c["service"] == "dashboard")
    portfolio_os = next(c for c in service["checks"] if c["service"] == "portfolio_os")
    committee = next(c for c in service["checks"] if c["service"] == "committee")

    check(postgres["status"] == "healthy", "Postgres healthy", postgres["detail"])
    check(market["status"] == "healthy", "Market Data healthy", market["detail"])
    check(dashboard["status"] == "healthy", "Dashboard healthy", dashboard["detail"])
    check(portfolio_os["status"] in {"healthy", "degraded"}, "Portfolio OS checked", portfolio_os["detail"])
    check(committee["status"] in {"healthy", "degraded"}, "Committee checked", committee["detail"])

    check(alerts["alert_status"] in {"clear", "active"}, "Alert engine ran", f"alerts={alerts['alert_count']}")
    check(audit["readiness"] in {"ready", "review_required"}, "Runtime audit ran", audit["readiness"])
    check(readiness["institutional_readiness_score"] >= 60, "Institutional readiness score acceptable")

    print("-" * 80)
    print(f"Institutional Readiness Score: {readiness['institutional_readiness_score']}/100")
    print(f"Status: {readiness['status']}")
    print("=" * 80)
    print("[PASS] PHASE 6A.5 RELIABILITY LAYER COMPLETE")
    print("AURUM now has self-monitoring reliability primitives.")
    print("=" * 80)


if __name__ == "__main__":
    main()