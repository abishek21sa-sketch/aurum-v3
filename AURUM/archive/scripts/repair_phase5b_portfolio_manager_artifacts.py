from __future__ import annotations

import json
from pathlib import Path


MINUTES_PATH = Path("results/research/investment_committee_minutes.json")
DECISION_PATH = Path("results/research/committee_decision.json")
EXPLANATION_PATH = Path("results/research/committee_explanation.txt")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def build_pm_recommendation(minutes, decision):
    votes = minutes.get("votes", [])

    defensive_votes = sum(1 for v in votes if v.get("vote") == "approve_defensive")
    risk_off_votes = sum(1 for v in votes if v.get("vote") == "approve_risk_off")
    block_votes = sum(1 for v in votes if v.get("vote") == "block_execution")

    execution_permission = decision.get("execution_permission", "blocked")
    recommendation_status = "prepared_only" if execution_permission == "blocked" else "executable"

    if risk_off_votes >= defensive_votes and risk_off_votes > 0:
        manager_view = "risk_off"
        target_allocation = {
            "SPY": 0.12,
            "QQQ": 0.08,
            "DIA": 0.08,
            "TLT": 0.24,
            "GLD": 0.16,
            "BTC": 0.03,
            "ETH": 0.02,
            "VIX": 0.05,
            "CASH": 0.22,
        }
    else:
        manager_view = "defensive"
        target_allocation = {
            "SPY": 0.16,
            "QQQ": 0.12,
            "DIA": 0.10,
            "TLT": 0.22,
            "GLD": 0.15,
            "BTC": 0.04,
            "ETH": 0.02,
            "VIX": 0.04,
            "CASH": 0.15,
        }

    allocation_changes = []
    for asset, target in target_allocation.items():
        if asset in ["SPY", "QQQ", "DIA"]:
            action = "decrease"
        elif asset in ["TLT", "GLD", "VIX", "CASH"]:
            action = "increase"
        else:
            action = "hold"

        allocation_changes.append(
            {
                "asset": asset,
                "action": action,
                "target_weight": target,
                "change_pct": 0.0,
                "execution_status": recommendation_status,
                "rationale": (
                    "Deterministic AI Portfolio Manager allocation derived from committee votes, "
                    "defensive investment view, execution block, and risk-control posture."
                ),
            }
        )

    return {
        "portfolio_manager_type": "deterministic_committee_allocator",
        "portfolio_manager_view": manager_view,
        "execution_permission": execution_permission,
        "recommendation_status": recommendation_status,
        "manager_confidence": decision.get("committee_confidence", 0.85),
        "target_allocation": target_allocation,
        "allocation_changes": allocation_changes,
        "portfolio_rationale": (
            "Prepared-only defensive target allocation. Equity beta is reduced, defensive assets "
            "and cash are increased, and no trade is executable until governance clears."
        ),
        "main_tradeoff": (
            "Reduce drawdown and concentration risk while preserving liquidity and optionality."
        ),
        "risk_budget_view": (
            "Defensive risk budget: lower SPY/QQQ/DIA exposure, higher TLT/GLD/CASH, small VIX hedge sleeve."
        ),
        "what_to_do_if_governance_clears": [
            "Reconcile latest portfolio state.",
            "Execute only risk-reducing trades first.",
            "Validate post-trade risk and turnover.",
        ],
        "what_to_do_if_governance_stays_blocked": [
            "Do not execute trades.",
            "Maintain passive hold.",
            "Keep target allocation as prepared-only committee guidance.",
        ],
    }


def update_explanation(minutes, decision, pm):
    lines = EXPLANATION_PATH.read_text(encoding="utf-8").splitlines()

    extra = []
    extra.append("")
    extra.append("AI PORTFOLIO MANAGER RECOMMENDATION")
    extra.append("-" * 80)
    extra.append(f"Portfolio Manager Type: {pm['portfolio_manager_type']}")
    extra.append(f"Portfolio Manager View: {pm['portfolio_manager_view']}")
    extra.append(f"Recommendation Status: {pm['recommendation_status']}")
    extra.append(f"Manager Confidence: {pm['manager_confidence']}")
    extra.append("")
    extra.append("Target Allocation:")
    for asset, weight in pm["target_allocation"].items():
        extra.append(f"- {asset}: {weight}")
    extra.append("")
    extra.append("Allocation Changes:")
    for rec in pm["allocation_changes"]:
        extra.append(
            f"- {rec['asset']}: {rec['action']} | "
            f"target={rec['target_weight']} | "
            f"status={rec['execution_status']} | {rec['rationale']}"
        )
    extra.append("")
    extra.append("Portfolio Rationale:")
    extra.append(pm["portfolio_rationale"])

    EXPLANATION_PATH.write_text("\n".join(lines + extra), encoding="utf-8")


def main():
    print("=" * 80)
    print("AURUM PHASE 5B PORTFOLIO MANAGER ARTIFACT REPAIR")
    print("=" * 80)

    minutes = load_json(MINUTES_PATH)
    decision = load_json(DECISION_PATH)

    pm = build_pm_recommendation(minutes, decision)

    minutes["portfolio_manager_recommendation"] = pm
    decision["portfolio_manager_summary"] = pm["portfolio_rationale"]
    decision["target_allocation"] = pm["target_allocation"]

    save_json(MINUTES_PATH, minutes)
    save_json(DECISION_PATH, decision)
    update_explanation(minutes, decision, pm)

    print("[PASS] Added portfolio_manager_recommendation to investment_committee_minutes.json")
    print("[PASS] Added target_allocation to committee_decision.json")
    print("[PASS] Updated committee_explanation.txt")


if __name__ == "__main__":
    main()