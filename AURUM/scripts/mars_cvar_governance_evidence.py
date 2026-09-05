from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.institutional.mars_cvar_decision_bridge import build_mars_cvar_decision
from src.institutional.mars_cvar_validation import (
    equal_weight_baseline,
    run_turnover_calibration,
    static_cvar_baseline,
    mean_variance_baseline,
)

OUT = ROOT / "artifacts" / "mars_cvar"


def problem():
    assets = ["SPY", "TLT", "GLD", "CASH"]
    returns = {
        "calm": np.array([[.018,.002,.003,.0002],[.012,.004,.002,.0002],[.021,-.001,.004,.0002]]),
        "stress": np.array([[-.08,.024,.035,.0002],[-.05,.017,.022,.0002],[-.11,.028,.040,.0002]]),
    }
    return assets, returns, [.35,.25,.20,.20], [.60,.60,.60,1.0]


def main():
    started = time.perf_counter()
    assets, returns, previous, caps = problem()
    regime_probs = {"calm": .5, "stress": .5}
    penalties = [0.0, .0002, .001, .002, .005, .01, .02, .05, .10]
    max_turnover = .40
    alpha = .95
    risk_aversion = .35
    min_cash = .10

    rows = run_turnover_calibration(
        assets=assets, regime_returns=returns, regime_probabilities=regime_probs,
        previous_weights=previous, max_weights=caps, penalties=penalties,
        alpha=alpha, risk_aversion=risk_aversion, min_cash=min_cash,
        max_turnover=max_turnover,
    )
    selected = next(r for r in rows if r["passes_turnover_gate"])

    decision = build_mars_cvar_decision(
        assets=assets, regime_returns=returns, regime_probabilities=regime_probs,
        previous_weights=previous, max_weights=caps, alpha=alpha,
        risk_aversion=risk_aversion, turnover_penalty=selected["turnover_penalty"],
        min_cash=min_cash, max_cvar_loss=.03, max_turnover=max_turnover,
    )
    static = static_cvar_baseline(
        assets=assets, regime_returns=returns, previous_weights=previous,
        max_weights=caps, alpha=alpha, risk_aversion=risk_aversion,
        turnover_penalty=selected["turnover_penalty"], min_cash=min_cash,
    )
    equal = equal_weight_baseline(assets, previous, returns, regime_probs, alpha=alpha)
    mv = mean_variance_baseline(assets=assets, regime_returns=returns, regime_probabilities=regime_probs, previous_weights=previous, max_weights=caps, alpha=alpha, risk_aversion=5.0, min_cash=min_cash)

    checks = {
        "calibration_contains_blocked_low_penalty": any(not r["passes_turnover_gate"] for r in rows[:4]),
        "selected_penalty_passes_turnover_gate": bool(selected["passes_turnover_gate"]),
        "governed_decision_authorized": bool(decision["authorized"]),
        "governed_decision_turnover_within_limit": decision["turnover"] <= max_turnover + 1e-12,
        "static_cvar_baseline_optimal": static.status == "OPTIMAL",
        "equal_weight_baseline_sums_to_one": abs(sum(equal["weights"].values()) - 1.0) < 1e-12,
        "mean_variance_baseline_sums_to_one": abs(sum(mv["weights"].values()) - 1.0) < 1e-9,
    }

    evidence = {
        "algorithm": "MARS-CVaR",
        "null_hypothesis": "In strict walk-forward evaluation, next-regime weighting does not improve tail/risk-adjusted performance relative to static CVaR, equal-weight, and mean-variance baselines after turnover costs.",
        "evidence_class": "deterministic synthetic formulation/behavior evidence",
        "claim_boundary": "Does not establish investment alpha, calibrated regime forecasts, or realized performance.",
        "parameters": {"alpha": alpha, "risk_aversion": risk_aversion, "max_turnover": max_turnover, "min_cash": min_cash},
        "selected_turnover_penalty": selected["turnover_penalty"],
        "governed_decision": decision,
        "baselines": {
            "static_cvar": {
                "expected_return": static.expected_return,
                "cvar_loss": static.cvar_loss,
                "turnover": static.turnover,
                "weights": {a: float(w) for a,w in zip(static.assets, static.weights)},
            },
            "equal_weight": equal,
            "mean_variance": mv,
        },
        "ablation": {
            "component_removed": "institutional turnover calibration/gate",
            "low_penalty": rows[1],
            "selected_calibrated": selected,
        },
        "runtime_seconds": time.perf_counter() - started,
        "checks": checks,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "governance_evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    with (OUT / "turnover_sensitivity.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["turnover_penalty","expected_return","cvar_loss_signed","cvar_downside_magnitude","turnover","passes_turnover_gate"])
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "turnover_penalty": r["turnover_penalty"],
                "expected_return": r["expected_return"],
                "cvar_loss_signed": r["cvar_loss"],
                "cvar_downside_magnitude": max(0.0, r["cvar_loss"]),
                "turnover": r["turnover"],
                "passes_turnover_gate": r["passes_turnover_gate"],
            })

    report = f"""# MARS-CVaR Governance Evidence\n\nEvidence class: deterministic synthetic formulation/behavior evidence.\n\n## Calibrated reference\n- Turnover penalty: {selected['turnover_penalty']:.4f}\n- Turnover: {selected['turnover']:.6f}\n- CVaR signed loss: {selected['cvar_loss']:.6f} (negative means the modeled tail return is positive)\n- CVaR downside magnitude: {max(0.0, selected['cvar_loss']):.6f}\n- Expected return: {selected['expected_return']:.6f}\n- Risk gate: {decision['risk_gate']}\n\n## Ablation\nRemoving effective turnover calibration (penalty={rows[1]['turnover_penalty']}) produces turnover {rows[1]['turnover']:.6f}, which breaches the {max_turnover:.2f} institutional turnover gate.\n\n## Baselines\n- Static-CVaR turnover: {static.turnover:.6f}; CVaR signed loss: {static.cvar_loss:.6f}\n- Equal-weight turnover: {equal['turnover']:.6f}; CVaR signed loss: {equal['cvar_loss']:.6f}\n\n## Claim boundary\nThis evidence tests formulation behavior and governance gates on a deterministic synthetic scenario. It does not establish investment alpha, calibrated regime forecasts, or realized performance.\n"""
    (OUT / "GOVERNANCE_REPORT.md").write_text(report, encoding="utf-8")
    passed = sum(bool(v) for v in checks.values())
    print(f"MARS_CVAR_GOVERNANCE={passed}/{len(checks)}")
    print(f"SELECTED_TURNOVER_PENALTY={selected['turnover_penalty']:.4f}")
    print(f"TURNOVER={selected['turnover']:.6f}")
    print(f"RISK_GATE={decision['risk_gate']}")
    if passed != len(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
