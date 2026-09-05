from pathlib import Path
import importlib
import json

from src.portfolio_os.research_firm_bridge import ResearchFirmPortfolioOSBridge


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
    print("AURUM PHASE 6C.1 RESEARCH FIRM → PORTFOLIO OS BRIDGE VALIDATION")
    print("=" * 80)

    importlib.import_module("src.portfolio_os.research_firm_bridge")
    check(True, "research firm bridge imports")

    bridge = ResearchFirmPortfolioOSBridge().build_bridge()

    path = Path("results/portfolio_os/research_firm_portfolio_os_bridge.json")

    check(path.exists(), "research_firm_portfolio_os_bridge.json exists")
    check(bridge["status"] in {"complete", "degraded"}, "bridge status valid", bridge["status"])
    check(bridge["research_firm_status"] == "complete", "research firm output consumed")
    check(bridge["cio_risk_posture"] != "unknown", "CIO risk posture consumed")
    check(bridge["cio_recommended_action"] != "unknown", "CIO recommended action consumed")
    check(bridge["cio_execution_permission"] != "unknown", "CIO execution permission consumed")
    check(bridge["top_alpha"] != "unknown", "top alpha consumed")
    check(bridge["primary_risk"] != "unknown", "primary risk consumed")
    check(bridge["portfolio_os_execution_guidance"], "Portfolio OS execution guidance generated")
    check(bridge["portfolio_os_message"], "Portfolio OS message generated")

    payload = json.loads(path.read_text(encoding="utf-8"))

    required_keys = [
        "research_firm_status",
        "cio_risk_posture",
        "cio_recommended_action",
        "cio_execution_permission",
        "top_alpha",
        "primary_risk",
        "portfolio_os_execution_guidance",
        "portfolio_os_message",
    ]

    for key in required_keys:
        check(key in payload, f"{key} saved in bridge artifact")

    print("=" * 80)
    print("[PASS] PHASE 6C.1 RESEARCH FIRM → PORTFOLIO OS BRIDGE COMPLETE")
    print("AURUM now exposes AI Research Firm intelligence to Portfolio OS.")
    print("=" * 80)


if __name__ == "__main__":
    main()