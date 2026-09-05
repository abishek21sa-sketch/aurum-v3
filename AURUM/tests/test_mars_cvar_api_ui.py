from fastapi.testclient import TestClient
from pathlib import Path
from src.api.main import app

def test_mars_api_reference_and_controls():
    c=TestClient(app); r=c.get('/v1/mars-cvar/reference'); assert r.status_code==200 and r.json()['algorithm']=='MARS-CVaR'
    p=c.post('/v1/mars-cvar/decision?stress_probability=.8&turnover_penalty=.1'); assert p.status_code==200; assert abs(p.json()['regime_probabilities']['stress']-.8)<1e-9

def test_mars_cvar_evidence_endpoint_exposes_workstation_sections():
    c=TestClient(app); r=c.get('/v1/mars-cvar/evidence?stress_probability=.8&alpha=.95')
    assert r.status_code == 200
    payload = r.json()
    assert payload['algorithm'] == 'MARS-CVaR'
    assert {'market_regime','portfolio_workspace','risk_lab','walk_forward_research','governance'} <= set(payload)
    assert payload['governance']['research_promotion'] == 'RESEARCH_ONLY'

def test_official_dashboard_has_dedicated_mars_surface():
    s=Path('dashboard/official_dashboard.py').read_text(encoding='utf-8');
    for token in ['MARS-CVaR Regime Allocation Council','Next-regime stress probability','Turnover penalty','Constraints / evidence gates']:
        assert token in s
