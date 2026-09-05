"""Strict chronological walk-forward validation for MARS-CVaR on bundled historical prices."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.stats import norm
from src.optimization.signature_algorithm import next_regime_probabilities, solve_mars_cvar
from src.institutional.mars_cvar_validation import mean_variance_baseline, static_cvar_baseline

@dataclass(frozen=True)
class WalkForwardSummary:
    periods:int; start:str; end:str; mars_sharpe:float; static_cvar_sharpe:float; equal_weight_sharpe:float; mean_variance_sharpe:float
    mars_cumulative_return:float; best_baseline_sharpe:float; bonferroni_psr:float; promotion_gate:str; no_lookahead:bool
    def to_dict(self): return asdict(self)

def _load_returns(root:Path)->pd.DataFrame:
    p=root/'data'/'digital_twin'/'historical_prices'; data={}
    for a in ['SPY','TLT','GLD']:
        df=pd.read_csv(p/f'{a}.csv',parse_dates=['date']).set_index('date')['close'].sort_index(); data[a]=df
    prices=pd.DataFrame(data).dropna(); r=prices.pct_change().dropna(); r['CASH']=0.0; return r

def _sharpe(x:np.ndarray)->float:
    x=np.asarray(x,float); sd=x.std(ddof=1)
    return float(x.mean()/sd*np.sqrt(252)) if len(x)>1 and sd>0 else 0.0

def _psr(observations:np.ndarray, benchmark_sharpe:float, trials:int=3)->float:
    r=np.asarray(observations,float); n=len(r)
    if n<4 or r.std(ddof=1)<=0: return 0.0
    sr=r.mean()/r.std(ddof=1)
    centered=(r-r.mean())/r.std(ddof=1); skew=float(np.mean(centered**3)); kurt=float(np.mean(centered**4))
    denom=max(1e-12,1-skew*sr+((kurt-1)/4)*(sr**2))
    z=(sr-benchmark_sharpe/np.sqrt(252))*math.sqrt(n-1)/math.sqrt(denom)
    p=float(norm.cdf(z)); return max(0.0,min(1.0,1-min(1.0,(1-p)*trials)))

def run_walk_forward(root:Path, *, start='2018-01-01', end='2025-01-01', train_window=252, rebalance=63)->tuple[WalkForwardSummary,pd.DataFrame]:
    returns=_load_returns(root); returns=returns[(returns.index>=pd.Timestamp('2015-01-01')) & (returns.index<pd.Timestamp(end))]
    indices=np.where(returns.index>=pd.Timestamp(start))[0]
    if len(indices)==0: raise ValueError('walk-forward start outside data range')
    first=max(int(indices[0]),train_window); assets=['SPY','TLT','GLD','CASH']; caps=[.60,.60,.60,1.0]; prev=np.array([.35,.25,.20,.20])
    rows=[]
    for i in range(first,len(returns)-rebalance,rebalance):
        train=returns.iloc[i-train_window:i].copy(); test=returns.iloc[i:i+rebalance].copy()
        spy=train['SPY']; vol=spy.rolling(20).std().bfill(); threshold=float(vol.median()); states=['stress' if v>threshold else 'calm' for v in vol]
        probs=next_regime_probabilities(states,['calm','stress'])
        arrays={k:train.loc[[s==k for s in states],assets].to_numpy(float) for k in ['calm','stress']}
        if min(len(v) for v in arrays.values())<10: continue
        mars=solve_mars_cvar(assets,arrays,probs,prev,max_weights=caps,alpha=.95,risk_aversion=.35,turnover_penalty=.05,min_cash=.10)
        static=static_cvar_baseline(assets=assets,regime_returns=arrays,previous_weights=prev,max_weights=caps,alpha=.95,risk_aversion=.35,turnover_penalty=.05,min_cash=.10)
        mv=mean_variance_baseline(assets=assets,regime_returns=arrays,regime_probabilities=probs,previous_weights=prev,max_weights=caps,alpha=.95,risk_aversion=5,min_cash=.10)
        eq=np.full(4,.25); realized=test[assets].to_numpy(float)
        for d,row in test.iterrows():
            rows.append({'date':d.date().isoformat(),'train_end':train.index[-1].date().isoformat(),'test_start':test.index[0].date().isoformat(),
              'mars':float(row[assets].to_numpy(float)@mars.weights),'static_cvar':float(row[assets].to_numpy(float)@static.weights),
              'equal_weight':float(row[assets].to_numpy(float)@eq),'mean_variance':float(row[assets].to_numpy(float)@np.array(list(mv['weights'].values()))),
              'stress_probability':float(probs['stress']),'turnover':float(mars.turnover)})
        prev=mars.weights.copy()
    df=pd.DataFrame(rows)
    if df.empty: raise RuntimeError('walk-forward produced no periods')
    sharpe={k:_sharpe(df[k].to_numpy()) for k in ['mars','static_cvar','equal_weight','mean_variance']}
    best=max(sharpe[k] for k in sharpe if k!='mars'); psr=_psr(df['mars'].to_numpy(),best,trials=3)
    no_lookahead=bool((pd.to_datetime(df['train_end']) < pd.to_datetime(df['test_start'])).all())
    promotion='ELIGIBLE_FOR_PAPER_REVIEW' if no_lookahead and sharpe['mars']>best and psr>=.95 else 'RESEARCH_ONLY'
    summary=WalkForwardSummary(len(df),str(df.date.iloc[0]),str(df.date.iloc[-1]),sharpe['mars'],sharpe['static_cvar'],sharpe['equal_weight'],sharpe['mean_variance'],float(np.prod(1+df['mars'])-1),best,psr,promotion,no_lookahead)
    return summary,df
