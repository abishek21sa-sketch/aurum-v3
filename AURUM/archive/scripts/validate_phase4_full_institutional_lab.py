from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import List, Tuple


PHASE4_MODULES = [
    # 4A / 4B / 4C / 4D existing real-time system modules
    "src.monitoring.event_stream_monitor",
    "src.research.strategy_registry",
    "src.research.strategy_stress_tester",
    "src.research.robustness_score_engine",
    "src.research.strategy_research_report",
    "src.dashboards.strategy_research_dashboard",
]

PHASE4_OUTPUTS = [
    # Research platform
    Path("results/research/strategy_registry.json"),
    Path("results/research/strategy_stress_results.csv"),
    Path("results/research/robustness_scores.csv"),
    Path("results/research/strategy_research_report.json"),
    Path("results/research/strategy_research_report.txt"),

    # Common live system outputs / folders
    Path("results/research"),
    Path("results/portfolio"),
    Path("results/optimization"),
    Path("results/monitoring"),
    Path("results/governance"),
    Path("results/execution"),
]


def pass_msg(msg: str) -> None:
    print(f"[PASS] {msg}")


def warn_msg(msg: str) -> None:
    print(f"[WARN] {msg}")


def fail_msg(msg: str) -> None:
    print(f"[FAIL] {msg}")


def check_imports() -> Tuple[bool, List[str]]:
    print("\nMODULE IMPORT CHECKS")
    print("-" * 80)

    ok = True
    failures = []

    for module in PHASE4_MODULES:
        try:
            importlib.import_module(module)
            pass_msg(module)
        except Exception as exc:
            ok = False
            failures.append(f"{module}: {exc}")
            fail_msg(f"{module} | {exc}")

    return ok, failures


def check_outputs() -> Tuple[bool, List[str]]:
    print("\nOUTPUT EXISTENCE CHECKS")
    print("-" * 80)

    ok = True
    failures = []

    for path in PHASE4_OUTPUTS:
        if path.exists():
            pass_msg(str(path))
        else:
            ok = False
            failures.append(str(path))
            fail_msg(str(path))

    return ok, failures


def run_research_pipeline() -> Tuple[bool, List[str]]:
    print("\nPHASE 4E RESEARCH PIPELINE CHECK")
    print("-" * 80)

    try:
        from src.research.strategy_registry import build_strategy_registry
        from src.research.strategy_stress_tester import stress_test_strategies
        from src.research.robustness_score_engine import calculate_robustness_scores
        from src.research.strategy_research_report import generate_strategy_research_report

        build_strategy_registry()
        stress_test_strategies()
        calculate_robustness_scores()
        generate_strategy_research_report()

        pass_msg("strategy research pipeline executed")
        return True, []

    except Exception as exc:
        fail_msg(f"strategy research pipeline failed | {exc}")
        return False, [str(exc)]


def check_stream_snapshot() -> Tuple[bool, List[str]]:
    print("\nREAL-TIME STREAM SNAPSHOT CHECK")
    print("-" * 80)

    try:
        import redis

        redis_url = "redis://localhost:6379/0"
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()

        required_streams = [
            "market_ticks",
            "market_features",
            "market_signals",
            "risk_events",
            "optimizer_events",
            "portfolio_decisions",
            "execution_orders",
            "trade_tickets",
            "alerts",
        ]

        missing = []

        for stream in required_streams:
            try:
                length = client.xlen(stream)
                if length > 0:
                    pass_msg(f"{stream} active | length={length}")
                else:
                    missing.append(stream)
                    warn_msg(f"{stream} exists but empty")
            except Exception:
                missing.append(stream)
                warn_msg(f"{stream} missing or unreadable")

        if missing:
            return False, missing

        return True, []

    except Exception as exc:
        warn_msg(f"Redis stream check skipped or failed | {exc}")
        return False, [str(exc)]


def write_validation_artifact(
    import_ok: bool,
    output_ok: bool,
    research_ok: bool,
    stream_ok: bool,
    import_failures: List[str],
    output_failures: List[str],
    research_failures: List[str],
    stream_failures: List[str],
) -> Path:
    out_dir = Path("results/phase4")
    out_dir.mkdir(parents=True, exist_ok=True)

    status = {
        "phase": "Phase 4",
        "name": "Real-Time Institutional Market Laboratory",
        "checks": {
            "module_imports": import_ok,
            "required_outputs": output_ok,
            "strategy_research_pipeline": research_ok,
            "redis_stream_snapshot": stream_ok,
        },
        "failures": {
            "module_imports": import_failures,
            "required_outputs": output_failures,
            "strategy_research_pipeline": research_failures,
            "redis_stream_snapshot": stream_failures,
        },
        "overall_status": "PASS"
        if import_ok and output_ok and research_ok
        else "PARTIAL",
        "note": (
            "Redis stream check may show PARTIAL if live services are not currently running. "
            "Backend artifacts are evaluated independently."
        ),
    }

    path = out_dir / "phase4_full_institutional_lab_validation.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    return path


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 4 FULL INSTITUTIONAL LAB VALIDATION")
    print("=" * 80)

    import_ok, import_failures = check_imports()
    research_ok, research_failures = run_research_pipeline()
    output_ok, output_failures = check_outputs()
    stream_ok, stream_failures = check_stream_snapshot()

    artifact = write_validation_artifact(
        import_ok,
        output_ok,
        research_ok,
        stream_ok,
        import_failures,
        output_failures,
        research_failures,
        stream_failures,
    )

    print("\nVALIDATION ARTIFACT")
    print("-" * 80)
    print(f"Saved: {artifact}")

    print("\nFINAL STATUS")
    print("-" * 80)

    if import_ok and output_ok and research_ok and stream_ok:
        print("[PASS] PHASE 4 FULL INSTITUTIONAL LAB VALIDATED")
    elif import_ok and output_ok and research_ok:
        print("[PASS/PARTIAL] PHASE 4 BACKEND VALIDATED; LIVE STREAMS NEED ACTIVE SERVICES")
    else:
        print("[FAIL] PHASE 4 FULL INSTITUTIONAL LAB INCOMPLETE")


if __name__ == "__main__":
    main()