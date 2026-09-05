import numpy as np
from src.optimization.signature_algorithm import laplace_transition_matrix, next_regime_probabilities, solve_mars_cvar

def sample():
    assets=["SPY","TLT","GLD","CASH"]
    returns={
      "calm":np.array([[.020,.003,.002,.0002],[.012,.002,.004,.0002],[.018,.001,.003,.0002]]),
      "stress":np.array([[-.08,.020,.030,.0002],[-.05,.015,.020,.0002],[-.10,.025,.040,.0002]])}
    return assets,returns

def test_transition_rows_stochastic():
    p=laplace_transition_matrix(["calm","calm","stress","calm"],["calm","stress"])
    assert np.allclose(p.sum(axis=1),1)

def test_next_probabilities_sum_one():
    p=next_regime_probabilities(["calm","stress","stress"],["calm","stress"])
    assert abs(sum(p.values())-1)<1e-12

def test_solver_feasible_and_capped():
    a,r=sample(); x=solve_mars_cvar(a,r,{"calm":.6,"stress":.4},[.35,.25,.2,.2],max_weights=[.6,.6,.6,1],min_cash=.1,risk_aversion=.5)
    assert x.status=="OPTIMAL"; assert abs(x.weights.sum()-1)<1e-8; assert x.weights[-1]>=.1-1e-8

def test_stress_probability_reduces_equity():
    a,r=sample(); kw=dict(previous_weights=[.35,.25,.2,.2],max_weights=[.7,.7,.7,1],risk_aversion=.35,turnover_penalty=.0001)
    calm=solve_mars_cvar(a,r,{"calm":.9,"stress":.1},**kw)
    stress=solve_mars_cvar(a,r,{"calm":.1,"stress":.9},**kw)
    assert stress.weights[0] <= calm.weights[0] + 1e-9
