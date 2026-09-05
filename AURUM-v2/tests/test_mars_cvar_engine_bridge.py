import json

from src.agents.mars_cvar_engine_bridge import load_mars_cvar_context


def test_bridge_reads_governed_mars_artifact_without_execution_rights(tmp_path):
    p = tmp_path / "mars.json"
    p.write_text(json.dumps({
        "algorithm": "MARS-CVaR",
        "status": "OPTIMAL",
        "decision_id": "MARS-TEST",
        "target_weights": {"SPY": .5, "CASH": .5},
        "risk_gate": "AUTHORIZED",
        "claim_boundary": "Optimization evidence only.",
        "expected_return": .01,
        "cvar_loss": .02,
        "turnover": .10,
        "regime_probabilities": {"calm": .6, "stress": .4},
    }), encoding="utf-8")
    ctx = load_mars_cvar_context(p)
    assert ctx["available"] is True
    assert ctx["governed"] is True
    assert ctx["decision_id"] == "MARS-TEST"
    assert ctx["execution_authorized"] is False


def test_bridge_fails_closed_on_incomplete_artifact(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text('{"algorithm":"MARS-CVaR"}', encoding="utf-8")
    ctx = load_mars_cvar_context(p)
    assert ctx["available"] is False
    assert ctx["execution_authorized"] is False
