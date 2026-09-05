from pathlib import Path
import yaml


def check(condition: bool, label: str):
    if condition:
        print(f"[PASS] {label}")
    else:
        print(f"[FAIL] {label}")
        raise SystemExit(1)


def main():
    print("=" * 80)
    print("AURUM PHASE 6A.6 DEPLOYMENT LAYER VALIDATION")
    print("=" * 80)

    compose_path = Path("docker-compose.yml")
    dashboard_dockerfile = Path("Dockerfile.dashboard")
    api_dockerfile = Path("Dockerfile.api")

    check(compose_path.exists(), "docker-compose.yml exists")
    check(dashboard_dockerfile.exists(), "Dockerfile.dashboard exists")
    check(api_dockerfile.exists(), "Dockerfile.api exists")

    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    services = compose.get("services", {})

    required_services = [
        "redis",
        "timescaledb",
        "api",
        "dashboard",
        "portfolio_os",
        "reliability",
    ]

    for service in required_services:
        check(service in services, f"{service} service configured")

    dashboard_cmd = dashboard_dockerfile.read_text(encoding="utf-8")
    check("dashboard/official_dashboard.py" in dashboard_cmd, "dashboard Dockerfile points to official dashboard")

    dashboard_env = services["dashboard"].get("environment", [])
    api_env = services["api"].get("environment", [])
    portfolio_env = services["portfolio_os"].get("environment", [])
    reliability_env = services["reliability"].get("environment", [])

    for name, env in [
        ("dashboard", dashboard_env),
        ("api", api_env),
        ("portfolio_os", portfolio_env),
        ("reliability", reliability_env),
    ]:
        check(
            any("TIMESCALE_DATABASE_URL" in item for item in env),
            f"{name} has Timescale env var",
        )
        check(
            any("REDIS_URL" in item for item in env),
            f"{name} has Redis env var",
        )

    check("8501:8501" in services["dashboard"].get("ports", []), "dashboard port mapped")
    check("8000:8000" in services["api"].get("ports", []), "api port mapped")
    check("5434:5432" in services["timescaledb"].get("ports", []), "Timescale port mapped")
    check("6379:6379" in services["redis"].get("ports", []), "Redis port mapped")

    check("healthcheck" in services["redis"], "Redis healthcheck configured")
    check("healthcheck" in services["timescaledb"], "Timescale healthcheck configured")

    print("=" * 80)
    print("[PASS] PHASE 6A.6 DEPLOYMENT LAYER COMPLETE")
    print("AURUM deployment stack is configured for docker compose.")
    print("=" * 80)


if __name__ == "__main__":
    main()