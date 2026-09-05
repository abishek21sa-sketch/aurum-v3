from pathlib import Path
import importlib
import json

from src.institutional.daily_institutional_cycle import DailyInstitutionalCycle


REQUIRED_STAGES = {
    "portfolio_os",
    "ai_research_firm",
    "research_firm_portfolio_os_bridge",
    "cio",
    "intelligence_persistence",
    "reliability",
}


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
    print("AURUM PHASE 6C.6 DAILY INSTITUTIONAL CYCLE VALIDATION")
    print("=" * 80)

    importlib.import_module("src.institutional.daily_institutional_cycle")
    importlib.import_module("src.institutional.daily_institutional_report_generator")
    check(True, "daily institutional modules import")

    cycle = DailyInstitutionalCycle().run()

    path = Path("results/institutional/daily_institutional_cycle.json")
    check(path.exists(), "daily_institutional_cycle.json exists")

    check(cycle["status"] in {"complete", "degraded"}, "cycle status valid", cycle["status"])
    check(cycle["stage_count"] >= 6, "at least 6 cycle stages executed", str(cycle["stage_count"]))

    stage_names = {stage["stage"] for stage in cycle["stages"]}

    for stage in REQUIRED_STAGES:
        check(stage in stage_names, f"{stage} stage executed")

    completed = [stage for stage in cycle["stages"] if stage["status"] == "complete"]
    check(len(completed) >= 5, "at least 5 stages completed", str(len(completed)))

    summary = cycle["executive_summary"]

    check(summary["best_alpha"] != "unknown", "best alpha included")
    check(summary["primary_risk"] != "unknown", "primary risk included")
    check(summary["cio_action"] != "unknown", "CIO action included")
    check(summary["cio_risk_posture"] != "unknown", "CIO risk posture included")
    check(summary["execution_permission"] != "unknown", "execution permission included")
    check(summary["readiness_score"] >= 60, "readiness score acceptable", str(summary["readiness_score"]))

    payload = json.loads(path.read_text(encoding="utf-8"))
    check(payload["executive_summary"]["interpretation"], "cycle interpretation saved")

    print("=" * 80)
    print("[PASS] PHASE 6C.6 DAILY INSTITUTIONAL CYCLE COMPLETE")
    print("AURUM now has one command for the daily institutional intelligence cycle.")
    print("=" * 80)


if __name__ == "__main__":
    main()