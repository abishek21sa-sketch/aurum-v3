import numpy as np

from src.institutional.mars_cvar_validation import (
    equal_weight_baseline,
    run_turnover_calibration,
    static_cvar_baseline,
)


def fixture():
    assets=["SPY","TLT","GLD","CASH"]
    returns={
      "calm":np.array([[.018,.002,.003,.0002],[.012,.004,.002,.0002],[.021,-.001,.004,.0002]]),
      "stress":np.array([[-.08,.024,.035,.0002],[-.05,.017,.022,.0002],[-.11,.028,.040,.0002]])}
    return assets, returns


def test_calibration_penalty_never_increases_turnover_materially():
    a,r=fixture()
    rows=run_turnover_calibration(assets=a,regime_returns=r,regime_probabilities={"calm":.5,"stress":.5},previous_weights=[.35,.25,.2,.2],max_weights=[.6,.6,.6,1],penalties=[0,.001,.005,.01,.02,.05],alpha=.95,risk_aversion=.35,min_cash=.1,max_turnover=.4)
    turns=[x["turnover"] for x in rows]
    assert all(b <= a + 1e-9 for a,b in zip(turns,turns[1:]))
    assert any(x["passes_turnover_gate"] for x in rows)


def test_baselines_are_explicit_and_feasible():
    a,r=fixture(); prev=[.35,.25,.2,.2]
    eq=equal_weight_baseline(a,prev,r,{"calm":.5,"stress":.5},alpha=.95)
    static=static_cvar_baseline(assets=a,regime_returns=r,previous_weights=prev,max_weights=[.6,.6,.6,1],alpha=.95,risk_aversion=.35,turnover_penalty=.01,min_cash=.1)
    assert eq["name"]=="equal_weight"
    assert abs(sum(eq["weights"].values())-1)<1e-12
    assert static.status=="OPTIMAL"
