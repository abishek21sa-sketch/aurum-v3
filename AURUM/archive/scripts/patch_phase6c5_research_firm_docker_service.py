from pathlib import Path


COMPOSE = Path("docker-compose.yml")


SERVICE_BLOCK = """
  research_firm:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: aurum-research-firm
    environment:
      - AURUM_ENV=development
      - TIMESCALE_DATABASE_URL=postgresql://aurum:aurum@timescaledb:5432/aurum
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
    depends_on:
      redis:
        condition: service_healthy
      timescaledb:
        condition: service_healthy
    command: ["python", "-m", "src.research_firm.ai_research_firm_mode"]
    restart: "no"
"""


def main() -> None:
    text = COMPOSE.read_text(encoding="utf-8")

    if "research_firm:" in text:
        print("[SKIP] research_firm service already exists")
        return

    marker = "\nvolumes:"
    if marker not in text:
        raise SystemExit("[FAIL] docker-compose.yml missing volumes marker")

    text = text.replace(marker, SERVICE_BLOCK + marker)

    COMPOSE.write_text(text, encoding="utf-8")

    print("[PASS] docker-compose.yml patched with research_firm service")


if __name__ == "__main__":
    main()