from pathlib import Path

import numpy as np
import pytest

from scripts.product_adapter import compute
from src.institutional.mars_cvar_product import build_reference_product_evidence
from src.optimization.signature_algorithm import solve_mars_cvar


ROOT = Path(__file__).resolve().parents[1]


def test_product_payload_exposes_institutional_workflow_and_separate_governance():
    evidence = build_reference_product_evidence(ROOT)
    assert evidence["algorithm"] == "MARS-CVaR"
    assert evidence["market_regime"]["transition_matrix_valid"]
    assert evidence["risk_lab"]["scenario_count"] == 6
    assert evidence["governance"]["optimization_authorization"] == "AUTHORIZED"
    assert evidence["governance"]["research_promotion"] == "RESEARCH_ONLY"
    assert evidence["governance"]["execution_enabled"] is False
    assert evidence["decision"]["solver"]["backend"] == "scipy.optimize.linprog"
    assert evidence["decision"]["feasibility"]["status"] == "FEASIBLE"
    assert evidence["decision"]["feasibility"]["portfolio_sum_residual"] < 1e-8
    assert sum(evidence["market_regime"]["decision_input_next_regime_probabilities"].values()) == pytest.approx(1.0)


def test_signed_cvar_is_explicit_in_product_display():
    decision = compute()
    labels = [row[0] for row in decision["metrics"]]
    assert "CVaR signed loss" in labels
    assert "Downside loss magnitude" in labels
    assert "signed loss" in decision["risk_lab"]["cvar_convention"]


def test_sweeps_are_real_solver_evaluations():
    evidence = build_reference_product_evidence(ROOT)
    assert len(evidence["frontier"]) == 5
    assert len(evidence["sensitivity"]["turnover_penalty"]) == 5
    assert len(evidence["sensitivity"]["stress_probability"]) == 5
    assert all("expected_return" in row and "turnover" in row for row in evidence["frontier"])


def test_invalid_probability_and_return_inputs_are_rejected():
    with pytest.raises(ValueError):
        solve_mars_cvar(
            ["A", "CASH"],
            {"calm": np.array([[0.01, 0.0]]), "stress": np.array([[0.0, 0.0]])},
            {"calm": np.nan, "stress": 1.0},
            [0.5, 0.5],
        )
