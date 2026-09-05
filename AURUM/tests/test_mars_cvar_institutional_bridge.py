import json
import numpy as np
from src.institutional.mars_cvar_decision_bridge import build_mars_cvar_decision, OUTPUT

def test_bridge_writes_governed_artifact(tmp_path, monkeypatch):
    import src.institutional.mars_cvar_decision_bridge as b
    monkeypatch.setattr(b,"OUTPUT",tmp_path/"decision.json")
    d=build_mars_cvar_decision(assets=["SPY","CASH"],regime_returns={"calm":np.array([[.02,.0002]]),"stress":np.array([[-.08,.0002]])},regime_probabilities={"calm":.5,"stress":.5},previous_weights=[.5,.5],max_weights=[.8,1],risk_aversion=1.0,min_cash=.1,max_cvar_loss=.03)
    assert d["decision_id"].startswith("MARS-")
    assert b.OUTPUT.exists()
    assert json.loads(b.OUTPUT.read_text(encoding='utf-8'))["algorithm"]=="MARS-CVaR"


def test_turnover_gate_blocks_excessive_rebalance(tmp_path, monkeypatch):
    import src.institutional.mars_cvar_decision_bridge as b
    monkeypatch.setattr(b,"OUTPUT",tmp_path/"decision.json")
    d=build_mars_cvar_decision(assets=["SPY","CASH"],regime_returns={"calm":np.array([[.03,.0002]]),"stress":np.array([[-.09,.0002]])},regime_probabilities={"calm":.5,"stress":.5},previous_weights=[.9,.1],max_weights=[.9,1],risk_aversion=1.0,min_cash=.1,max_cvar_loss=.2,max_turnover=.2)
    assert d["turnover"] > .2
    assert d["risk_gate"] == "BLOCKED"
    assert "turnover" in d["blocked_reasons"]
