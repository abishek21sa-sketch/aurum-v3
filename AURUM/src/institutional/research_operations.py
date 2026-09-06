"""Deterministic research-operations surface for the AURUM product.

This is the governed bridge between the portfolio decision surface and the
research-firm workflows represented by the original AURUM repositories:
hypothesis tracking, statistical validation, adversarial review, research
memory, continuous-learning checks, and mission control.  It deliberately
uses the current decision evidence as its source of truth and does not claim
that a fixture is a live research run.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


RESEARCH_SCHEMA_VERSION = "1.0"
HYPOTHESIS_ID = "H-MARS-001"


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _decision_from_artifact(root: Path) -> dict[str, Any]:
    payload = _read_json(root / "artifacts" / "product_runtime" / "latest_product_evidence.json")
    decision = payload.get("decision")
    return decision if isinstance(decision, dict) else {}


def _manifest_summary(root: Path, directory: str, filename: str) -> dict[str, Any]:
    manifest = _read_json(root / "artifacts" / directory / filename)
    inferred_status = "PASS" if manifest.get("actual_rows") else "REVIEW"
    return {
        "status": manifest.get("status") or inferred_status,
        "data_class": manifest.get("data_class", "UNKNOWN"),
        "source_count": manifest.get("source_count", manifest.get("sources", 0)),
        "artifact": f"artifacts/{directory}/{filename}",
    }


def _validation(decision: dict[str, Any]) -> dict[str, Any]:
    walk = decision.get("walk_forward_research", {})
    summary = walk.get("summary", {}) if isinstance(walk, dict) else {}
    periods = int(_number(summary.get("periods"), 0))
    mars_sharpe = _number(summary.get("mars_sharpe"), 0.0)
    baseline = _number(summary.get("best_baseline_sharpe"), 0.0)
    no_lookahead = bool(walk.get("no_lookahead"))
    checks = [
        {
            "id": "walk_forward_complete",
            "label": "Walk-forward window complete",
            "status": "PASS" if periods > 0 else "REVIEW",
            "value": f"{periods} periods",
            "evidence": "walk_forward_evidence.json",
        },
        {
            "id": "no_lookahead",
            "label": "No-lookahead boundary",
            "status": "PASS" if no_lookahead else "BLOCKED",
            "value": str(no_lookahead).lower(),
            "evidence": "walk_forward_research.no_lookahead",
        },
        {
            "id": "sample_size",
            "label": "Independent sample-size floor",
            "status": "PASS" if periods >= 30 else "REVIEW",
            "value": f"{periods} >= 30",
            "evidence": "research validation contract",
        },
        {
            "id": "baseline_uplift",
            "label": "Incremental uplift over best baseline",
            "status": "PASS" if mars_sharpe > baseline + 1e-9 else "REVIEW",
            "value": f"{mars_sharpe:.3f} vs {baseline:.3f} Sharpe",
            "evidence": "walk_forward_research.summary",
        },
        {
            "id": "promotion_gate",
            "label": "Empirical promotion gate",
            "status": "BLOCKED" if decision.get("research_promotion") != "PROMOTED" else "PASS",
            "value": str(decision.get("research_promotion", "RESEARCH_ONLY")),
            "evidence": "governance.research_promotion",
        },
    ]
    passed = sum(item["status"] == "PASS" for item in checks)
    return {
        "method": "governed_reference_validation",
        "checks": checks,
        "checks_passed": passed,
        "checks_total": len(checks),
        "status": "PASS" if passed == len(checks) else "REVIEW",
        "promotion_safe": False,
        "claim_boundary": "Reference walk-forward evidence is not realized performance and does not establish investment alpha.",
        "metrics": {
            "periods": periods,
            "mars_sharpe": round(mars_sharpe, 6),
            "best_baseline_sharpe": round(baseline, 6),
            "bonferroni_psr": summary.get("bonferroni_psr"),
        },
    }


def _committee(decision: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    risk = decision.get("risk_lab", {}) if isinstance(decision.get("risk_lab"), dict) else {}
    turnover = _number((decision.get("transaction_analysis") or {}).get("aggregate_l1_turnover"))
    baseline = validation["metrics"].get("best_baseline_sharpe", 0.0)
    mars = validation["metrics"].get("mars_sharpe", 0.0)
    objection = (
        f"The reference MARS Sharpe ({mars:.3f}) does not exceed the best baseline ({baseline:.3f}); "
        "the current evidence therefore does not establish incremental alpha."
    )
    return {
        "mode": "LOCAL_GROUNDED_COMMITTEE_FIXTURE",
        "decision": "RESEARCH_ONLY",
        "decision_label": "Hold for further research",
        "judge_engaged_bear_objection": True,
        "agents": [
            {
                "role": "Bull",
                "position": "Investigate",
                "summary": "Stress-aware CVaR allocation has a coherent risk-management thesis and a complete walk-forward artifact.",
            },
            {
                "role": "Bear",
                "position": "Do not promote",
                "summary": objection,
            },
            {
                "role": "Risk",
                "position": "Constrain",
                "summary": f"L1 turnover is {turnover:.2%}; tail scenarios are reference-class evidence with {risk.get('scenario_count', 0)} scenarios.",
            },
            {
                "role": "Judge",
                "position": "Request evidence",
                "summary": "Keep the hypothesis in research-only status until independent uplift, cost realism, and reviewable external evidence are added.",
            },
        ],
        "strongest_bear_objection": objection,
        "conditions_for_next_review": [
            "Add independent public-data validation with a frozen manifest and freshness record.",
            "Test transaction costs, capacity, and turnover sensitivity on the same time split.",
            "Run an independent out-of-time window and document multiple-testing controls.",
        ],
        "execution_enabled": False,
        "research_promotion": "RESEARCH_ONLY",
    }


def _memory(decision: dict[str, Any]) -> list[dict[str, Any]]:
    turnover = _number((decision.get("transaction_analysis") or {}).get("aggregate_l1_turnover"))
    return [
        {
            "memory_id": "RM-001",
            "failure_mode": "no_incremental_baseline_edge",
            "lesson": "A complete backtest is not enough when the optimized lens ties its strongest baseline.",
            "structured_constraint": "Require independent out-of-sample uplift before empirical promotion.",
            "applies_when": "The candidate Sharpe is not greater than the best baseline after the same split.",
            "source": HYPOTHESIS_ID,
            "status": "ACTIVE_CONSTRAINT",
        },
        {
            "memory_id": "RM-002",
            "failure_mode": "implementation_friction",
            "lesson": f"The current reference decision carries {turnover:.2%} L1 turnover, so liquidity and cost review must remain visible.",
            "structured_constraint": "Do not treat target weights as implementable without cost and capacity evidence.",
            "applies_when": "Aggregate turnover is material or the target move is concentrated.",
            "source": "transaction_analysis",
            "status": "ACTIVE_CONSTRAINT",
        },
        {
            "memory_id": "RM-003",
            "failure_mode": "scenario_class_boundary",
            "lesson": "Simulated reference scenarios can explain a tail convention but cannot be presented as a live loss forecast.",
            "structured_constraint": "Carry evidence_class and source lineage into every scenario-derived conclusion.",
            "applies_when": "Scenario data is synthetic, simulated, or reference-only.",
            "source": "risk_lab.scenarios",
            "status": "ACTIVE_CONSTRAINT",
        },
    ]


def _learning(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "NOT_STARTED",
        "stage": "RESEARCH_ONLY",
        "paper_trading_enabled": False,
        "decay_monitor": {
            "status": "BLOCKED_BY_GOVERNANCE",
            "required_windows": ["out_of_time", "transaction_cost", "regime_slice"],
            "metrics": ["Sharpe", "CVaR", "max_drawdown", "turnover", "calibration"],
        },
        "next_evaluation": "Create an independently frozen evaluation window before any paper-trading consideration.",
        "boundary": decision.get("claim", "Research evidence only"),
    }


def _mission_control(root: Path, decision: dict[str, Any]) -> dict[str, Any]:
    public = _manifest_summary(root, "public_data", "public_data_manifest.json")
    synthetic = _manifest_summary(root, "synthetic", "synthetic_ml_dataset_manifest.json")
    components = [
        {"name": "Decision engine", "status": "READY", "mode": "MARS-CVaR reference solver"},
        {"name": "AI intelligence", "status": "READY", "mode": "local grounded / human-gated"},
        {"name": "Public evidence", "status": public["status"], "mode": public["data_class"]},
        {"name": "Synthetic ML", "status": synthetic["status"], "mode": synthetic["data_class"]},
        {"name": "Execution", "status": "DISABLED", "mode": "no orders emitted"},
    ]
    return {
        "cycle_status": "READY",
        "cycle_mode": "DETERMINISTIC_RESEARCH_CYCLE",
        "last_decision_id": decision.get("decision_id"),
        "components": components,
        "timeline": [
            {"stage": "Observe", "status": "PASS", "detail": "Decision and public-evidence artifacts loaded."},
            {"stage": "Validate", "status": "REVIEW", "detail": "Validation contract is visible; promotion remains blocked."},
            {"stage": "Challenge", "status": "PASS", "detail": "Bear objection and risk challenge are recorded."},
            {"stage": "Decide", "status": "REVIEW", "detail": "Judge outcome is research-only; no order or promotion path exists."},
            {"stage": "Learn", "status": "BLOCKED", "detail": "Requires an independently frozen out-of-time evaluation."},
        ],
        "scheduler": {"status": "NOT_CONFIGURED", "note": "A deterministic request-driven cycle is active; no hidden background scheduler is running."},
        "execution_enabled": False,
    }


def _digital_twin(decision: dict[str, Any]) -> dict[str, Any]:
    risk = decision.get("risk_lab", {}) if isinstance(decision.get("risk_lab"), dict) else {}
    scenarios = risk.get("scenarios", []) if isinstance(risk.get("scenarios"), list) else []
    return {
        "status": "REFERENCE_SCENARIOS",
        "scenario_count": len(scenarios),
        "evidence_class": "SIMULATED_REFERENCE_SCENARIO",
        "scenarios": [
            {
                "scenario_id": item.get("scenario_id"),
                "regime": item.get("regime"),
                "portfolio_return": item.get("portfolio_return"),
                "signed_loss": item.get("signed_loss"),
                "in_cvar_tail": item.get("in_cvar_tail"),
            }
            for item in scenarios
        ],
        "boundary": "Digital-twin scenarios are analytical counterfactuals, not live forecasts or execution instructions.",
    }


def build_research_operations(root: Path, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the complete, read-only research operations payload."""
    decision = decision or _decision_from_artifact(root)
    validation = _validation(decision)
    payload: dict[str, Any] = {
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "service": "AURUM Research Operations",
        "mode": "DETERMINISTIC_GOVERNED_FIXTURE",
        "generated_at_utc": _now_utc(),
        "execution_enabled": False,
        "research_promotion": "RESEARCH_ONLY",
        "hypotheses": [
            {
                "hypothesis_id": HYPOTHESIS_ID,
                "title": "Regime-conditioned CVaR allocation with turnover control",
                "thesis": "A regime-aware CVaR lens may reduce tail exposure while preserving a reviewable implementation path when turnover and evidence boundaries are explicit.",
                "status": "RESEARCH_ONLY",
                "stage": "STATISTICAL_REVIEW",
                "priority": "HIGH",
                "universe": "SPY / TLT / GLD / CASH",
                "holding_period": "reference period",
                "evidence_refs": [
                    "artifacts/mars_cvar/walk_forward_evidence.json",
                    "artifacts/public_data/public_data_manifest.json",
                    "artifacts/synthetic/synthetic_ml_validation.json",
                ],
                "next_action": "Independent out-of-time validation",
            }
        ],
        "validation": validation,
        "committee": _committee(decision, validation),
        "memory": _memory(decision),
        "learning": _learning(decision),
        "mission_control": _mission_control(root, decision),
        "digital_twin": _digital_twin(decision),
        "lineage": [
            {"from": "decision", "to": HYPOTHESIS_ID, "relationship": "research hypothesis derived from governed evidence"},
            {"from": HYPOTHESIS_ID, "to": "validation", "relationship": "evaluated by reference walk-forward checks"},
            {"from": "validation", "to": "committee", "relationship": "challenged by Bull/Bear/Risk/Judge fixture"},
            {"from": "committee", "to": "memory", "relationship": "constraints retained for future experiments"},
            {"from": "memory", "to": "learning", "relationship": "out-of-time evaluation required before decay monitoring"},
        ],
        "next_actions": [
            "Freeze an independent public-data evaluation window and hash the manifest.",
            "Add transaction-cost and capacity assumptions to the same research ticket.",
            "Replace the deterministic committee fixture with a schema-validated optional model provider.",
        ],
    }
    unsigned = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    payload["artifact_integrity"] = {
        "content_sha256": hashlib.sha256(unsigned).hexdigest(),
        "hash_scope": "all fields except artifact_integrity",
    }
    return payload


def write_research_operations(root: Path, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = build_research_operations(root, decision)
    path = root / "artifacts" / "research_operations" / "latest_research_operations.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return payload


def build_research_feed(root: Path, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = build_research_operations(root, decision)
    return {
        "schema_version": payload["schema_version"],
        "service": payload["service"],
        "status": payload["validation"]["status"],
        "hypotheses": payload["hypotheses"],
        "validation": payload["validation"],
        "next_actions": payload["next_actions"],
        "research_promotion": payload["research_promotion"],
        "execution_enabled": payload["execution_enabled"],
    }


def build_research_memory(root: Path, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = build_research_operations(root, decision)
    return {
        "schema_version": payload["schema_version"],
        "service": payload["service"],
        "memories": payload["memory"],
        "count": len(payload["memory"]),
        "execution_enabled": False,
        "research_promotion": "RESEARCH_ONLY",
    }
