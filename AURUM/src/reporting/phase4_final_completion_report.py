from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


OUTPUT_DIR = Path("results/phase4")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

READINESS_PATH = Path("results/institutional/institutional_readiness_report.json")
RUNTIME_PATH = Path("results/institutional/latest_institutional_runtime_state.json")
CANONICAL_STATE_PATH = Path("results/institutional/canonical_runtime_state.json")
EXPLANATION_PATH = Path("results/institutional/decision_explanation.json")
LINEAGE_PATH = Path("results/institutional/decision_lineage.json")

OUTPUT_JSON = OUTPUT_DIR / "phase4_final_completion_report.json"
OUTPUT_TXT = OUTPUT_DIR / "phase4_final_completion_report.txt"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def generate_phase4_final_completion_report() -> Dict[str, Any]:
    readiness = load_json(READINESS_PATH)
    runtime = load_json(RUNTIME_PATH)
    canonical = load_json(CANONICAL_STATE_PATH)
    explanation = load_json(EXPLANATION_PATH)
    lineage = load_json(LINEAGE_PATH)

    report = {
        "project": "AURUM",
        "phase": "Phase 4",
        "phase_name": "Real-Time Institutional Market Laboratory",
        "completion_status": "COMPLETE_RESEARCH_GRADE_PLUS",
        "production_status": "NOT_PRODUCTION_RELEASED",
        "readiness": {
            "overall_status": readiness.get("overall_status"),
            "platform_score": readiness.get("platform_score"),
            "research_ready": readiness.get("research_ready"),
            "production_ready": readiness.get("production_ready"),
            "runtime_integrity_status": readiness.get("runtime_integrity_status"),
            "coherence_gate_status": readiness.get("coherence_gate_status"),
            "governance_status": readiness.get("governance_status"),
            "execution_release_allowed": readiness.get("execution_release_allowed"),
        },
        "runtime_summary": runtime.get("summary", {}),
        "canonical_state": {
            "current_regime": canonical.get("current_regime"),
            "state_label": canonical.get("state_label"),
            "stress_score": canonical.get("stress_score"),
            "risk_level": canonical.get("risk_level"),
            "portfolio_action": canonical.get("portfolio_action"),
            "decision_reason": canonical.get("decision_reason"),
            "governance_status": canonical.get("governance_status"),
            "readiness_status": canonical.get("readiness_status"),
            "consistency_status": canonical.get("consistency_status"),
            "allow_execution": canonical.get("allow_execution"),
        },
        "decision_explanation": {
            "decision": explanation.get("decision"),
            "confidence": explanation.get("confidence"),
            "institutional_summary": explanation.get("institutional_summary"),
            "execution_permission": explanation.get("execution_permission"),
        },
        "decision_lineage": {
            "decision_chain_id": lineage.get("decision_chain_id"),
            "lineage_status": lineage.get("lineage_quality", {}).get("lineage_status"),
            "missing_nodes": lineage.get("lineage_quality", {}).get("missing_nodes"),
        },
        "completed_capabilities": [
            "Real-time Redis stream infrastructure",
            "Streaming market ticks and features",
            "Live digital twin state",
            "Real-time risk projection",
            "Real-time portfolio decision generation",
            "Execution order generation",
            "Trade ticket generation",
            "Execution governance checks",
            "Runtime integrity audit",
            "Runtime coherence gate",
            "Canonical runtime state synchronizer",
            "Institutional decision cycle orchestrator",
            "Institutional readiness report",
            "Portfolio laboratory engine",
            "Portfolio laboratory dashboard",
            "Strategy research platform",
            "Stress testing and robustness scoring",
            "Strategy research dashboard",
            "Institutional command center",
            "Canonical runtime state engine",
            "Decision explanation engine",
            "Decision lineage engine",
            "Phase 4 readiness and closeout reporting",
        ],
        "remaining_before_production": [
            "Replace demo/synthetic market data with production-grade live data provider",
            "Automate continuous refresh of risk, optimizer, execution, governance, and ticket streams",
            "Resolve timestamp sequencing so every runtime cycle has strict lineage ordering",
            "Enable production execution release only after gate_status becomes ALLOW",
            "Add broker/exchange integration, credentials, order acknowledgements, rejects, and fills",
            "Add persistent audit database and immutable decision_chain_id propagation across all services",
            "Move from research assumptions to live market-data, broker, and risk-model calibration",
        ],
        "phase4_final_verdict": (
            "AURUM Phase 4 is complete as a research-grade institutional real-time market laboratory. "
            "It includes real-time infrastructure, digital twin state, risk projection, portfolio decisioning, "
            "execution artifacts, governance, portfolio laboratory, strategy research, canonical runtime state, "
            "decision explanation, and decision lineage. It is intentionally not production-released because "
            "market data is demo/synthetic and the coherence gate correctly blocks execution."
        ),
        "phase5_recommendation": (
            "Proceed to Phase 5 after freezing Phase 4. Phase 5 should add AI Research Desk, "
            "AI Investment Committee, AI Risk Committee, AI Portfolio Manager, market memory, "
            "multi-agent debate, and decision reasoning."
        ),
    }

    save_report(report)
    return report


def save_report(report: Dict[str, Any]) -> None:
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM PHASE 4 FINAL COMPLETION REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Phase Name: Real-Time Institutional Market Laboratory")
    lines.append("Completion Status: COMPLETE_RESEARCH_GRADE_PLUS")
    lines.append("Production Status: NOT_PRODUCTION_RELEASED")
    lines.append("")
    lines.append("READINESS")
    lines.append("-" * 80)

    for key, value in report["readiness"].items():
        lines.append(f"{key}: {value}")

    lines.append("")
    lines.append("CANONICAL RUNTIME STATE")
    lines.append("-" * 80)

    for key, value in report["canonical_state"].items():
        lines.append(f"{key}: {value}")

    lines.append("")
    lines.append("DECISION EXPLANATION")
    lines.append("-" * 80)

    for key, value in report["decision_explanation"].items():
        lines.append(f"{key}: {value}")

    lines.append("")
    lines.append("DECISION LINEAGE")
    lines.append("-" * 80)

    for key, value in report["decision_lineage"].items():
        lines.append(f"{key}: {value}")

    lines.append("")
    lines.append("COMPLETED CAPABILITIES")
    lines.append("-" * 80)

    for item in report["completed_capabilities"]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("REMAINING BEFORE PRODUCTION")
    lines.append("-" * 80)

    for item in report["remaining_before_production"]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("FINAL VERDICT")
    lines.append("-" * 80)
    lines.append(report["phase4_final_verdict"])

    lines.append("")
    lines.append("PHASE 5 RECOMMENDATION")
    lines.append("-" * 80)
    lines.append(report["phase5_recommendation"])

    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    result = generate_phase4_final_completion_report()

    print("=" * 80)
    print("AURUM PHASE 4 FINAL COMPLETION REPORT")
    print("=" * 80)
    print(f"Completion Status: {result['completion_status']}")
    print(f"Production Status: {result['production_status']}")
    print(f"Decision Chain: {result['decision_lineage']['decision_chain_id']}")
    print(f"Saved: {OUTPUT_JSON}")
    print(f"Saved: {OUTPUT_TXT}")