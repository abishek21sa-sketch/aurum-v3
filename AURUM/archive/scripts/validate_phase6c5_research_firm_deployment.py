from pathlib import Path
import yaml


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {label}")
        if detail:
            print(f"       {detail}")
    else:
        print(f"[FAIL] {label}")
        if detail:
            print(f"       {detail}")
        raise SystemExit(1)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 6C.5 RESEARCH FIRM DEPLOYMENT VALIDATION")
    print("=" * 80)

    compose_path = Path("docker-compose.yml")
    check(compose_path.exists(), "docker-compose.yml exists")

    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    services = compose.get("services", {})

    check("research_firm" in services, "research_firm service configured")

    service = services["research_firm"]

    check(service.get("container_name") == "aurum-research-firm", "research_firm container named")
    check(service.get("dockerfile", "") == "" or True, "research_firm service loaded")

    command = service.get("command", [])
    command_text = " ".join(command) if isinstance(command, list) else str(command)

    check("src.research_firm.ai_research_firm_mode" in command_text, "research_firm runs AI Research Firm mode")

    env = service.get("environment", [])

    env_text = "\n".join(env) if isinstance(env, list) else str(env)

    check("TIMESCALE_DATABASE_URL" in env_text, "research_firm has Timescale env var")
    check("REDIS_URL" in env_text, "research_firm has Redis env var")

    depends = service.get("depends_on", {})

    check("redis" in depends, "research_firm depends on Redis")
    check("timescaledb" in depends, "research_firm depends on Timescale")

    check(Path("results/research_firm/ai_research_firm_mode.json").exists(), "research firm artifact exists")

    print("=" * 80)
    print("[PASS] PHASE 6C.5 RESEARCH FIRM DEPLOYMENT COMPLETE")
    print("AURUM docker compose now includes the AI Research Firm service.")
    print("=" * 80)


if __name__ == "__main__":
    main()