from pathlib import Path
from src.institutional.mars_cvar_walk_forward import run_walk_forward
ROOT=Path(__file__).resolve().parents[1]
def test_walk_forward_is_strictly_chronological_and_has_all_baselines():
    s,df=run_walk_forward(ROOT,start='2023-01-01',end='2024-07-01',train_window=126,rebalance=63)
    assert s.no_lookahead and len(df)>100
    assert {'mars','static_cvar','equal_weight','mean_variance'} <= set(df.columns)
    assert s.promotion_gate in {'ELIGIBLE_FOR_PAPER_REVIEW','RESEARCH_ONLY'}
