from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.institutional.mars_cvar_walk_forward import run_walk_forward
OUT=ROOT/'artifacts'/'mars_cvar'; OUT.mkdir(parents=True,exist_ok=True)
s,df=run_walk_forward(ROOT); df.to_csv(OUT/'walk_forward_daily.csv',index=False)
p={'null_hypothesis':'MARS-CVaR does not improve out-of-sample risk-adjusted performance relative to static-CVaR/equal-weight/mean-variance after turnover costs.','evidence_class':'historical observational walk-forward backtest','summary':s.to_dict(),'claim_boundary':'Historical walk-forward evidence is not realized future performance and does not establish investment alpha.'}
(OUT/'walk_forward_evidence.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
print('MARS_WALK_FORWARD_PERIODS='+str(s.periods)); print('MARS_NO_LOOKAHEAD='+str(s.no_lookahead)); print('MARS_PROMOTION_GATE='+s.promotion_gate); print('MARS_SHARPE='+f'{s.mars_sharpe:.4f}'); print('BEST_BASELINE_SHARPE='+f'{s.best_baseline_sharpe:.4f}'); print('BONFERRONI_PSR='+f'{s.bonferroni_psr:.4f}')
