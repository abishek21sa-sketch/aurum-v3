from __future__ import annotations
import numpy as np
from src.institutional.mars_cvar_decision_bridge import build_mars_cvar_decision

def canonical_inputs(stress_probability:float=.50,turnover_penalty:float=.05)->dict:
    stress=float(stress_probability); calm=1-stress
    return dict(
      assets=['SPY','TLT','GLD','CASH'],
      regime_returns={
        'calm':np.array([[.018,.002,.003,.0002],[.012,.004,.002,.0002],[.021,-.001,.004,.0002]]),
        'stress':np.array([[-.08,.024,.035,.0002],[-.05,.017,.022,.0002],[-.11,.028,.040,.0002]])},
      regime_probabilities={'calm':calm,'stress':stress},previous_weights=[.35,.25,.20,.20],max_weights=[.60,.60,.60,1.0],
      alpha=.95,risk_aversion=.35,turnover_penalty=float(turnover_penalty),min_cash=.10,max_cvar_loss=.03,max_turnover=.40)

def build_reference_mars_decision(stress_probability:float=.50,turnover_penalty:float=.05,*,persist:bool=False)->dict:
    """Build the reference decision without mutating artifacts by default."""
    return build_mars_cvar_decision(**canonical_inputs(stress_probability,turnover_penalty), persist=persist)
