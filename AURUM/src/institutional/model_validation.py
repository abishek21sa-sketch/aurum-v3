"""Independent model-validation packet for the MARS-CVaR research build."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def _check(check_id: str, status: str, summary: str, **details: Any) -> dict[str, Any]:
    return {"check_id": check_id, "status": status, "summary": summary, "details": details}


def build_model_validation(root: Path, evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if evidence is None:
        from src.institutional.mars_cvar_product import build_reference_product_evidence

        evidence = build_reference_product_evidence(root)
    decision = evidence.get("decision", {})
    risk = evidence.get("risk_lab", {})
    research = evidence.get("walk_forward_research", {})
    research_summary = research.get("summary", {})
    governance = evidence.get("governance", {})
    provenance = evidence.get("data_provenance", {})
    baselines = evidence.get("baselines", [])
    checks = [
        _check("validation.no_lookahead", "PASS" if research.get("no_lookahead") is True else "FAIL", "Walk-forward process declares no lookahead", value=research.get("no_lookahead")),
        _check("validation.null_hypothesis", "PASS" if research.get("null_hypothesis") else "FAIL", "A falsifiable research null hypothesis is recorded", present=bool(research.get("null_hypothesis"))),
        _check("validation.baseline_comparators", "PASS" if len(baselines) >= 3 else "FAIL", "At least three comparator strategies are retained", comparator_count=len(baselines)),
        _check("validation.transaction_cost_awareness", "PASS" if "turnover" in decision and evidence.get("transaction_analysis") else "FAIL", "Turnover and implementation-cost evidence is present", turnover=decision.get("turnover")),
        _check("validation.scenario_coverage", "PASS" if risk.get("scenario_count", 0) and risk.get("scenarios") else "FAIL", "Tail-risk scenarios carry explicit evidence", scenario_count=risk.get("scenario_count")),
        _check("validation.cvar_convention", "PASS" if str(risk.get("cvar_convention", "")).startswith("signed loss") else "FAIL", "Signed CVaR convention is documented", convention=risk.get("cvar_convention")),
        _check("validation.provenance_classification", "PASS" if provenance.get("decision_data_class") and provenance.get("scenario_data_class") else "FAIL", "Input and scenario evidence classes are disclosed", decision_data_class=provenance.get("decision_data_class"), scenario_data_class=provenance.get("scenario_data_class")),
        _check("validation.governance_separation", "PASS" if governance.get("execution_enabled") is False and governance.get("research_promotion") == "RESEARCH_ONLY" else "FAIL", "Execution and promotion remain separated", execution_enabled=governance.get("execution_enabled"), research_promotion=governance.get("research_promotion")),
    ]
    failures = [item for item in checks if item["status"] == "FAIL"]
    return {
        "schema_version": "1.0",
        "service": "AURUM independent model-validation packet",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "decision_id": decision.get("decision_id"),
        "status": "READY_FOR_INDEPENDENT_REVIEW" if not failures else "BLOCKED",
        "internal_checks": checks,
        "summary": {"total_checks": len(checks), "passed_checks": len(checks) - len(failures), "failed_checks": len(failures), "walk_forward_periods": research_summary.get("periods")},
        "independent_review_required": True,
        "review_scope": [
            "Reproduce the walk-forward split and verify no-lookahead controls.",
            "Challenge scenario construction, tail convention, and transaction-cost assumptions.",
            "Compare results against independent implementation and adverse parameter perturbations.",
            "Approve or reject any future research-promotion request separately from optimizer authorization.",
        ],
        "promotion_state": "RESEARCH_ONLY",
        "execution_enabled": False,
        "claim_boundary": "Internal checks prepare an independent validation packet; they do not constitute independent validation or investment approval.",
    }
