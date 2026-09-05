from pathlib import Path

dash = Path("dashboard/aurum_mission_control.py").read_text(encoding="utf-8")

# Fix 1: Remove the ugly "Cycle count / 1" at the top
old_cycle = '''st.write("Cycle count")
st.code(runner_status.get("cycle_count", "N/A"))'''
new_cycle = '''# cycle count removed from header'''

# Fix 2: Replace bland header with institutional dark header
old_header = '''st.markdown('<div class="aurum-title">AURUM Mission Control</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="aurum-subtitle">LIVE institutional command center for market intelligence, AI agents, CIO directives, governance, portfolio posture, risk, and digital twin simulation.</div>',
    unsafe_allow_html=True,
)
st.markdown('<span class="live-pill">● LIVE</span>', unsafe_allow_html=True)
st.caption(f"Current Dashboard Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")'''

new_header = '''# Institutional header
_now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
_cycle = runner_status.get("cycle_count", 0)
_regime_hdr = str(mc.get("current_regime", "")).upper() or "LOADING"
_regime_hex = {"DEFENSIVE": "#d97706", "BULL": "#16a34a", "BEAR": "#dc2626", "HIGH_VOL": "#dc2626"}.get(_regime_hdr, "#6b7280")

st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
     border-radius:16px;padding:1.5rem 2rem;margin-bottom:1rem;
     border:1px solid #334155;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div style="color:#94a3b8;font-size:0.75rem;letter-spacing:.15em;text-transform:uppercase;margin-bottom:4px;">
        AURUM MISSION CONTROL
      </div>
      <div style="color:white;font-size:2rem;font-weight:800;letter-spacing:-0.5px;line-height:1;">
        Institutional AI Portfolio Intelligence
      </div>
      <div style="color:#64748b;font-size:0.85rem;margin-top:6px;">
        Real-time regime detection · CVaR optimization · Live paper trading · AI copilot
      </div>
    </div>
    <div style="text-align:right;">
      <div style="display:inline-flex;align-items:center;gap:6px;background:#052e16;
           border:1px solid #16a34a;border-radius:999px;padding:4px 12px;margin-bottom:8px;">
        <div style="width:8px;height:8px;background:#4ade80;border-radius:50%;
             animation:pulse 2s infinite;"></div>
        <span style="color:#4ade80;font-size:0.8rem;font-weight:700;">LIVE</span>
      </div>
      <div style="color:#94a3b8;font-size:0.75rem;">{_now_str}</div>
      <div style="color:#475569;font-size:0.72rem;">Cycle #{_cycle}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)'''

# Fix 3: Better CSS — tighter spacing, darker feel
old_css_block = '''.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}'''

new_css_block = '''.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f8fafc;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 0.82rem;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}'''

# Fix 4: Infrastructure cards — use text not cards to avoid wrapping
old_infra_cards = '''        i1, i2, i3, i4 = st.columns(4)
        with i1:
            card("Redis", redis_info.get("status", "unknown"), redis_color)
        with i2:
            card("Streams", redis_info.get("active_streams", 0), "green")
        with i3:
            card("TimescaleDB", ts_status, ts_color)
        with i4:
            card("Feed", provider_summary.get("active_feed", "unknown"), "blue")'''

new_infra_cards = '''        _redis_st = redis_info.get("status", "unknown")
        _streams = redis_info.get("active_streams", 0)
        _feed = provider_summary.get("active_feed", "unknown")
        _redis_dot = "🟢" if _redis_st == "connected" else "🔴"
        _ts_dot = "🟢" if ts_status == "connected" else "🟡"
        st.markdown(f"""
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:0.5rem;">
  <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:0.5rem 0.8rem;font-size:0.82rem;">
    {_redis_dot} <b>Redis</b> {_redis_st} · {_streams} streams
  </div>
  <div style="background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:0.5rem 0.8rem;font-size:0.82rem;">
    {_ts_dot} <b>TimescaleDB</b> {ts_status}
  </div>
  <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:0.5rem 0.8rem;font-size:0.82rem;">
    📡 <b>Feed</b> {_feed}
  </div>
</div>
""", unsafe_allow_html=True)'''

changes = 0
for old, new in [
    (old_cycle, new_cycle),
    (old_header, new_header),
    (old_css_block, new_css_block),
    (old_infra_cards, new_infra_cards),
]:
    if old in dash:
        dash = dash.replace(old, new)
        changes += 1
        print(f"Applied: {old.splitlines()[0].strip()[:55]}")
    else:
        print(f"NOT FOUND: {old.splitlines()[0].strip()[:55]}")

Path("dashboard/aurum_mission_control.py").write_text(dash, encoding="utf-8")

import py_compile
py_compile.compile("dashboard/aurum_mission_control.py", doraise=True)
print(f"\nSyntax OK. {changes}/4 changes applied.")