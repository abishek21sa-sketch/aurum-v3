from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from src.institutional.mars_cvar_decision_bridge import build_mars_cvar_decision

def main():
    d=build_mars_cvar_decision(
      assets=["SPY","TLT","GLD","CASH"],
      regime_returns={
        "calm":np.array([[.018,.002,.003,.0002],[.012,.004,.002,.0002],[.021,-.001,.004,.0002]]),
        "stress":np.array([[-.08,.024,.035,.0002],[-.05,.017,.022,.0002],[-.11,.028,.040,.0002]])},
      regime_probabilities={"calm":.5,"stress":.5},
      previous_weights=[.35,.25,.20,.20], max_weights=[.60,.60,.60,1.0],
      alpha=.95,risk_aversion=.35,turnover_penalty=.05,min_cash=.10,max_cvar_loss=.03,max_turnover=.40)
    print(f"MARS_CVAR_DECISION={d['decision_id']}")
    print(f"STATUS={d['status']}")
    print(f"RISK_GATE={d['risk_gate']}")
    print(f"CVAR_LOSS_SIGNED={d['cvar_loss']:.6f}")
    print(f"CVAR_DOWNSIDE_MAGNITUDE={max(0.0, d['cvar_loss']):.6f}")
    print(f"TURNOVER={d['turnover']:.6f}")
if __name__=='__main__': main()
