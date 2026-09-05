from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
from urllib.parse import parse_qs, urlparse
import urllib.request
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from product_adapter import (  # noqa: E402
    PROJECT,
    ALGORITHM,
    SUBTITLE,
    PORT,
    CONTROLS,
    DEFAULTS,
    DEMO_STRESS,
    compute,
)


ARTIFACT = ROOT / "artifacts" / "product_runtime" / "latest_product_evidence.json"


def prepare_demo() -> dict:
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    decision = compute(DEFAULTS)
    counterfactual = compute(DEMO_STRESS)
    payload = {
        "project": PROJECT,
        "algorithm": ALGORITHM,
        "mode": "DETERMINISTIC_PORTFOLIO_DEMO",
        "parameters": DEFAULTS,
        "decision": decision,
        "counterfactual": counterfactual,
        "evidence_boundary": decision["claim"],
        "runtime_contract": "institutional evidence surface over the repository-native MARS-CVaR LP; human review remains mandatory",
    }
    ARTIFACT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"{ALGORITHM}_PRODUCT_DEMO_PREPARED=PASS")
    print(f"DECISION_ID={decision['decision_id']}")
    return payload


def _html() -> str:
    page = r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__PROJECT__</title>
<style>
:root{--bg:#080b12;--panel:#111827;--panel2:#0d1421;--ink:#e5e7eb;--muted:#98a2b3;--accent:#e3b341;--line:#273246;--ok:#7dd3a8;--warn:#f6c85f;--bad:#ef8b8b}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,Segoe UI,Arial,sans-serif;font-size:14px} header{padding:26px 34px 20px;border-bottom:1px solid var(--line);background:linear-gradient(135deg,#0b111d,#101725)}
.eyebrow{font-size:11px;letter-spacing:.16em;color:var(--accent);font-weight:800;text-transform:uppercase}.sub{max-width:1100px;color:var(--muted);line-height:1.5;margin-top:8px} h1{font-size:28px;margin:7px 0 0} h2{font-size:17px;margin:0 0 13px} h3{font-size:14px;color:var(--accent);margin:20px 0 10px}.shell{display:grid;grid-template-columns:265px 1fr;gap:18px;padding:18px;max-width:1600px;margin:auto}.panel,.section{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:17px}.section{margin-bottom:16px}.side{align-self:start;position:sticky;top:12px}.side h2{margin-bottom:4px}.side-note{font-size:12px;line-height:1.45;color:var(--muted)}label{display:block;font-size:12px;margin:14px 0 5px;color:var(--muted)}input{width:100%;padding:9px;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:7px}button{width:100%;margin-top:16px;padding:10px;border:0;border-radius:7px;background:var(--accent);color:#111;font-weight:800;cursor:pointer}.nav{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:16px}.nav button{width:auto;margin:0;background:var(--panel);color:var(--muted);border:1px solid var(--line);padding:8px 11px}.nav button.active{color:#111;background:var(--accent)}.tab{display:none}.tab.active{display:block}.status{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:15px}.chips{display:flex;gap:8px;flex-wrap:wrap}.chip{border:1px solid var(--line);padding:6px 9px;border-radius:999px;font-size:12px}.chip.ok{color:var(--ok)}.chip.warn{color:var(--warn)}.chip.bad{color:var(--bad)}.cards{display:grid;grid-template-columns:repeat(5,minmax(125px,1fr));gap:9px}.card{background:var(--panel2);border:1px solid var(--line);padding:12px;border-radius:9px}.card small{display:block;color:var(--muted);font-size:11px}.card strong{display:block;margin-top:6px;font-size:19px}.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{padding:8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--muted);font-weight:600}td.num{text-align:right;font-variant-numeric:tabular-nums}.bar{height:8px;background:#1e293b;border-radius:99px;overflow:hidden;min-width:80px}.bar i{display:block;height:100%;background:var(--accent)}.muted{color:var(--muted)}.claim{color:var(--muted);line-height:1.5;border-left:3px solid var(--accent);padding-left:11px}.notice{background:#111c2b;border:1px solid var(--line);padding:11px;border-radius:8px;color:var(--muted);line-height:1.45}.scroll{overflow:auto}pre{white-space:pre-wrap;font-size:11px;max-height:500px;overflow:auto;background:var(--panel2);padding:12px;border-radius:8px}a{color:var(--accent)}ul{margin-top:7px;padding-left:20px;color:var(--muted);line-height:1.5}@media(max-width:1000px){.shell{grid-template-columns:1fr}.side{position:static}.cards{grid-template-columns:repeat(2,minmax(120px,1fr))}.grid2,.grid3{grid-template-columns:1fr}}
</style></head>
<body><header><div class="eyebrow">MARS-CVaR · HUMAN-GATED QUANTITATIVE RESEARCH</div><h1>__PROJECT__</h1><div class="sub">__SUBTITLE__</div></header>
<div class="shell"><aside class="panel side"><h2>Decision controls</h2><div class="side-note">Controls are governed counterfactual inputs to the repository-native optimizer. They do not place orders or promote a strategy.</div><div id="controls"></div><button onclick="runDecision()">Recompute evidence</button><p class="side-note">Offline acceptance uses the bundled deterministic reference fixture. Live data is optional and never a silent fallback.</p></aside>
<main><div class="status"><div><span class="muted">Decision ID</span> <strong id="decisionId">-</strong></div><div class="chips"><span class="chip" id="auth">Optimization authorization: -</span><span class="chip" id="promotion">Research promotion: -</span></div></div>
<nav class="nav"><button class="active" data-tab="overview">Overview</button><button data-tab="market">Market / Regime</button><button data-tab="portfolio">Portfolio</button><button data-tab="risk">Risk Lab</button><button data-tab="research">Research / Baselines</button><button data-tab="stress">Stress / Frontier</button><button data-tab="evidence">Evidence / Provenance</button></nav>
<section id="tab-overview" class="tab active"><div class="section"><h2>Decision overview</h2><div class="cards" id="metrics"></div><div class="grid2"><div><h3>Current to target</h3><div id="overviewActions"></div></div><div><h3>Governance boundary</h3><div id="overviewGovernance"></div></div></div></div><div class="section"><h2>What this result does and does not say</h2><div class="claim" id="claim"></div></div></section>
<section id="tab-market" class="tab"><div class="section"><h2>Market and regime command view</h2><div id="marketSummary"></div><div class="grid2"><div><h3>Transition matrix</h3><div id="transition"></div></div><div><h3>Next-regime decision input</h3><div id="regimeProbabilities"></div></div></div></div></section>
<section id="tab-portfolio" class="tab"><div class="section"><h2>Portfolio construction workspace</h2><div class="scroll" id="portfolioTable"></div><h3>Expected return contribution</h3><div class="scroll" id="contributions"></div></div><div class="section"><h2>Constraint monitor</h2><div class="scroll" id="constraints"></div></div><div class="section"><h2>Transaction and turnover analysis</h2><div id="turnoverSummary"></div><div class="scroll" id="trades"></div></div></section>
<section id="tab-risk" class="tab"><div class="section"><h2>CVaR risk lab</h2><div class="notice" id="riskConvention"></div><div class="grid3" id="riskSummary"></div><h3>Scenario tail evidence</h3><div class="scroll" id="scenarios"></div></div></section>
<section id="tab-research" class="tab"><div class="section"><h2>Baseline lab and promotion governance</h2><div class="scroll" id="baselines"></div><div class="grid2"><div><h3>Walk-forward validation</h3><div id="walkForward"></div></div><div><h3>Promotion state</h3><div id="researchGovernance"></div></div></div></div></section>
<section id="tab-stress" class="tab"><div class="section"><h2>Regime counterfactual and stress testing</h2><div id="counterfactual"></div><h3>Stress sensitivity</h3><div class="scroll" id="stressSensitivity"></div></div><div class="section"><h2>Risk-return and turnover frontier</h2><div class="notice">These points are solved LP evaluations. Binding caps and piecewise policy changes can create kinks; no continuity is implied.</div><div class="scroll" id="frontier"></div><h3>Turnover penalty sensitivity</h3><div class="scroll" id="turnoverSensitivity"></div></div></section>
<section id="tab-evidence" class="tab"><div class="section"><h2>Decision evidence and provenance</h2><div id="provenance"></div><p><a href="/download/evidence.json">Download the latest evidence JSON</a></p><details><summary>Raw auditable payload</summary><pre id="raw"></pre></details></div></section>
</main></div>
<script>
const controls=__CONTROLS__;
function esc(x){return String(x??'').replace(/[&<>]/g,s=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[s]))}
function val(x,d=4){return x===null||x===undefined?'N/A':(typeof x==='number'?x.toFixed(d):esc(x))}
function table(rows){if(!rows||!rows.length)return '<span class="muted">No evidence available.</span>';const keys=Object.keys(rows[0]);return '<table><thead><tr>'+keys.map(k=>'<th>'+esc(k)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+keys.map(k=>'<td>'+esc(r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}
function chips(d){document.getElementById('decisionId').textContent=d.decision_id;const a=document.getElementById('auth');a.textContent='Optimization authorization: '+d.optimization_authorization;a.className='chip '+(d.optimization_authorization==='AUTHORIZED'?'ok':'bad');const p=document.getElementById('promotion');p.textContent='Research promotion: '+d.research_promotion;p.className='chip '+(d.research_promotion==='RESEARCH_ONLY'?'warn':'ok')}
function render(d){chips(d);document.getElementById('metrics').innerHTML=d.metrics.map(x=>'<div class="card"><small>'+esc(x[0])+'</small><strong>'+esc(x[1])+'</strong></div>').join('');document.getElementById('claim').textContent=d.claim;document.getElementById('overviewActions').innerHTML=table(d.actions);document.getElementById('overviewGovernance').innerHTML='<div class="notice">'+esc(d.governance.separation_note)+'</div><ul><li>Human review required: '+d.governance.human_review_required+'</li><li>Execution enabled: '+d.governance.execution_enabled+'</li></ul>';
const m=d.market_regime;document.getElementById('marketSummary').innerHTML='<div class="grid3"><div class="card"><small>Current regime</small><strong>'+esc(m.current_regime)+'</strong></div><div class="card"><small>Normalized probability entropy</small><strong>'+val(m.probability_entropy_normalized)+'</strong></div><div class="card"><small>Transition matrix valid</small><strong>'+m.transition_matrix_valid+'</strong></div></div><p class="muted">'+esc(m.probability_vector_source)+'</p>';
document.getElementById('transition').innerHTML=table(Object.entries(m.transition_matrix).map(([r,v])=>({regime:r,...v,row_sum:m.transition_matrix_row_sums[r]})));const probs=m.decision_input_next_regime_probabilities;document.getElementById('regimeProbabilities').innerHTML=Object.entries(probs).map(([k,v])=>'<p>'+esc(k)+' <b>'+val(v*100,1)+'%</b></p><div class="bar"><i style="width:'+Math.max(0,Math.min(100,v*100))+'%"></i></div>').join('')+'<p class="muted">Estimated from transition matrix: '+JSON.stringify(m.estimated_next_regime_probabilities)+'</p>';
const pw=d.portfolio_workspace;document.getElementById('portfolioTable').innerHTML=table(d.actions);document.getElementById('contributions').innerHTML=table(pw.asset_contributions);document.getElementById('constraints').innerHTML=table(d.constraints);const ta=d.transaction_analysis;document.getElementById('turnoverSummary').innerHTML='<div class="grid3"><div class="card"><small>L1 turnover</small><strong>'+val(ta.aggregate_l1_turnover*100,2)+'%</strong></div><div class="card"><small>One-way turnover</small><strong>'+val(ta.one_way_turnover*100,2)+'%</strong></div><div class="card"><small>Penalty tau</small><strong>'+val(ta.turnover_penalty,4)+'</strong></div></div><p class="muted">'+esc(ta.turnover_definition)+'</p>';document.getElementById('trades').innerHTML=table(ta.trades);
const risk=d.risk_lab;document.getElementById('riskConvention').textContent=risk.cvar_convention;document.getElementById('riskSummary').innerHTML=[['Confidence alpha',val(risk.confidence_alpha,2)],['Signed CVaR',val(risk.cvar_loss_signed*100,3)+'%'],['Downside magnitude',val(risk.downside_loss_magnitude*100,3)+'%']].map(x=>'<div class="card"><small>'+x[0]+'</small><strong>'+x[1]+'</strong></div>').join('');document.getElementById('scenarios').innerHTML=table(risk.scenarios.map(x=>({...x,asset_returns:JSON.stringify(x.asset_returns)}))); 
document.getElementById('baselines').innerHTML=table(d.baselines);const wf=d.walk_forward_research;document.getElementById('walkForward').innerHTML=table(Object.entries(wf.summary||{}).map(([k,v])=>({metric:k,value:v})))+'<p class="muted">'+esc(wf.claim_boundary)+'</p>';document.getElementById('researchGovernance').innerHTML='<div class="notice"><b>'+esc(d.research_promotion)+'</b><br>Promotion is empirical and remains separate from optimization authorization.</div>';
const cf=arguments.length>1?arguments[1]:null;document.getElementById('counterfactual').innerHTML=cf?'<div class="grid2"><div><h3>Current decision</h3>'+table(d.actions)+'</div><div><h3>Counterfactual decision</h3>'+table(cf.actions)+'</div></div>':'<div class="notice">Recompute a decision to populate a counterfactual view.</div>';document.getElementById('stressSensitivity').innerHTML=table(d.sensitivity.stress_probability);document.getElementById('frontier').innerHTML=table(d.frontier);document.getElementById('turnoverSensitivity').innerHTML=table(d.sensitivity.turnover_penalty);const pr=d.data_provenance;document.getElementById('provenance').innerHTML=table(Object.entries(pr).map(([k,v])=>({field:k,value:Array.isArray(v)?v.join(', '):v})));document.getElementById('raw').textContent=JSON.stringify(d.raw,null,2)}
async function runDecision(){const q=new URLSearchParams();controls.forEach(c=>q.set(c.key,document.getElementById(c.key).value));const r=await fetch('/api/decision?'+q.toString());const d=await r.json();if(d.error){alert(d.detail||d.error);return}render(d)}
document.getElementById('controls').innerHTML=controls.map(c=>'<label>'+esc(c.label)+'</label><input id="'+esc(c.key)+'" type="number" min="'+c.min+'" max="'+c.max+'" step="'+c.step+'" value="'+c.default+'">').join('');document.querySelectorAll('.nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById('tab-'+b.dataset.tab).classList.add('active')});
fetch('/api/evidence').then(r=>r.json()).then(x=>render(x.decision,x.counterfactual));
</script></body></html>'''
    return page.replace("__PROJECT__", json.dumps(PROJECT)[1:-1]).replace("__SUBTITLE__", json.dumps(SUBTITLE)[1:-1]).replace("__CONTROLS__", json.dumps(CONTROLS))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/health":
                return self._send(200, json.dumps({"status": "ok", "project": PROJECT, "algorithm": ALGORITHM, "surface": "institutional-research-workstation"}).encode())
            if parsed.path == "/":
                return self._send(200, _html().encode("utf-8"), "text/html; charset=utf-8")
            if parsed.path == "/api/evidence":
                payload = json.loads(ARTIFACT.read_text(encoding="utf-8")) if ARTIFACT.exists() else prepare_demo()
                return self._send(200, json.dumps(payload, default=str).encode())
            if parsed.path == "/api/decision":
                query = parse_qs(parsed.query)
                params = {c["key"]: float(query.get(c["key"], [c["default"]])[0]) for c in CONTROLS}
                decision = compute(params)
                payload = {"project": PROJECT, "algorithm": ALGORITHM, "mode": "INTERACTIVE", "parameters": params, "decision": decision}
                ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
                ARTIFACT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
                return self._send(200, json.dumps(decision, default=str).encode())
            if parsed.path == "/download/evidence.json":
                payload = ARTIFACT.read_bytes() if ARTIFACT.exists() else json.dumps(prepare_demo(), indent=2).encode()
                return self._send(200, payload, "application/json")
            return self._send(404, b'{"detail":"not found"}')
        except Exception as exc:
            return self._send(500, json.dumps({"error": type(exc).__name__, "detail": str(exc)}).encode())

    def log_message(self, fmt: str, *args) -> None:
        print("[product]", fmt % args)


def serve(*, open_browser: bool = True) -> None:
    if not ARTIFACT.exists():
        prepare_demo()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"PRODUCT_RUNTIME_READY={url}", flush=True)
    if open_browser:
        webbrowser.open(url, new=2)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping product runtime...")
    finally:
        server.server_close()


def acceptance() -> None:
    payload = prepare_demo()
    decision = payload["decision"]
    required = {"market_regime", "portfolio_workspace", "risk_lab", "constraints", "frontier", "walk_forward_research", "data_provenance", "governance"}
    missing = required.difference(decision)
    if missing:
        raise SystemExit(f"PRODUCT_RUNTIME_ACCEPTANCE=FAIL missing_sections={sorted(missing)}")
    if decision["optimization_authorization"] not in ("AUTHORIZED", "BLOCKED"):
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL invalid optimization authorization")
    if decision["research_promotion"] != "RESEARCH_ONLY":
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL research promotion was silently changed")
    changed = payload["counterfactual"]
    if changed["decision_id"] == decision["decision_id"] and changed["raw"] == decision["raw"]:
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL counterfactual did not change")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for path in ("/health", "/", "/api/evidence", "/download/evidence.json"):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=20) as response:
                if response.status != 200:
                    raise SystemExit(f"PRODUCT_RUNTIME_ACCEPTANCE=FAIL http={path}:{response.status}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    if not ARTIFACT.exists():
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL evidence artifact missing")
    print(f"{ALGORITHM}_PRODUCT_RUNTIME_ACCEPTANCE=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-demo", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--accept", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.prepare_demo:
        prepare_demo()
    if args.accept:
        acceptance()
    if args.serve:
        serve(open_browser=not args.no_browser)
    if not (args.prepare_demo or args.accept or args.serve):
        parser.print_help()


if __name__ == "__main__":
    main()
