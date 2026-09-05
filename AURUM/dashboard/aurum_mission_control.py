from __future__ import annotations

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Any
import subprocess
import threading
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env before any imports that need API keys
import os as _os
_env_path = ROOT / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            _os.environ[_k.strip()] = _v.strip()

from src.mission_control.run_aurum_mission_control import run_mission_control_cycle
from src.mission_control.copilot_service import load_context, answer_question

ROOT = Path(__file__).resolve().parents[1]
MISSION_DIR = ROOT / "results" / "mission_control"

DASHBOARD_STATE_PATH = MISSION_DIR / "dashboard_state.json"
RECOMMENDATION_CARD_PATH = MISSION_DIR / "recommendation_card.json"
AGENT_ACTIVITY_PATH = MISSION_DIR / "agent_activity.jsonl"
COPILOT_RESPONSE_PATH = MISSION_DIR / "copilot_response.json"
PORTFOLIO_STATE_PATH = MISSION_DIR / "portfolio_state.json"
RUNNER_STATUS_PATH = MISSION_DIR / "runner_status.json"
PROVIDER_STATUS_PATH = MISSION_DIR / "provider_status.json"
INFRA_STATUS_PATH = MISSION_DIR / "infrastructure_status.json"
AGENT_HEALTH_PATH = MISSION_DIR / "agent_health.json"

# --- Auto-scheduler ---
_scheduler_started = False

def _background_cycle(interval_seconds: int = 300) -> None:
    """Runs the mission control cycle every N seconds in the background."""
    while True:
        try:
            run_mission_control_cycle()
        except Exception as e:
            pass
        time.sleep(interval_seconds)

def start_scheduler(interval_seconds: int = 300) -> None:
    """Start background scheduler once per Streamlit session."""
    global _scheduler_started
    if not _scheduler_started:
        t = threading.Thread(
            target=_background_cycle,
            args=(interval_seconds,),
            daemon=True,
        )
        t.start()
        _scheduler_started = True

start_scheduler(interval_seconds=300)


st.set_page_config(
    page_title="AURUM Mission Control",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.block-container {
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
}

.aurum-title {
    font-size: 3.0rem;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 0;
}

.aurum-subtitle {
    color: #8a8f98;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

.live-pill {
    display: inline-block;
    background: #10291d;
    color: #4ade80;
    border: 1px solid #22c55e;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-weight: 700;
    margin-bottom: 1rem;
}

.card {
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 1.1rem 1.2rem;
    background: white;
    box-shadow: 0 2px 10px rgba(0,0,0,0.035);
    min-height: 140px;
}

.card-label {
    color: #6b7280;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: .35rem;
}

.card-value {
    font-size: clamp(0.9rem, 2vw, 1.7rem);
    font-weight: 750;
    color: #111827;
    word-break: break-word;
}

.card-green {
    border-left: 6px solid #22c55e;
}

.card-red {
    border-left: 6px solid #ef4444;
}

.card-yellow {
    border-left: 6px solid #f59e0b;
}

.card-blue {
    border-left: 6px solid #3b82f6;
}

.timeline-item {
    border-left: 3px solid #d1d5db;
    padding-left: 1rem;
    padding-bottom: 1rem;
    margin-left: .5rem;
}

.timeline-agent {
    font-weight: 800;
}

.timeline-time {
    color: #6b7280;
    font-size: .8rem;
}

.success-text { color: #16a34a; font-weight: 800; }
.warning-text { color: #d97706; font-weight: 800; }
.critical-text { color: #dc2626; font-weight: 800; }
.info-text { color: #2563eb; font-weight: 800; }

.big-risk {
    background: #fff7ed;
    border: 1px solid #fdba74;
    border-radius: 14px;
    padding: 1rem;
    font-size: 1.2rem;
    font-weight: 700;
}

.action-box {
    background: #eff6ff;
    border: 1px solid #93c5fd;
    border-radius: 14px;
    padding: 1rem;
}

.next-box {
    background: #ecfdf5;
    border: 1px solid #86efac;
    border-radius: 14px;
    padding: 1rem;
    font-weight: 700;
}
</style>
""",
    unsafe_allow_html=True,
)


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def read_jsonl(path: Path, limit: int = 100) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
            if line.strip():
                events.append(json.loads(line))
    except Exception:
        return []
    return events


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def pct(x: Any) -> str:
    try:
        return f"{float(x) * 100:.2f}%"
    except Exception:
        return "N/A"


def fmt(x: Any) -> str:
    if x is None or x == "":
        return "N/A"
    if isinstance(x, float):
        return f"{x:.4f}"
    return str(x)


def severity_class(sev: str) -> str:
    sev = str(sev).lower()
    if sev == "success":
        return "success-text"
    if sev == "warning":
        return "warning-text"
    if sev == "critical":
        return "critical-text"
    return "info-text"


def card(label: str, value: Any, color: str = "blue") -> None:
    val = fmt(value)
    vlen = len(str(val))
    if vlen > 15:
        font_size = "0.95rem"
    elif vlen > 8:
        font_size = "1.2rem"
    else:
        font_size = "1.7rem"
    st.markdown(
        f"""
<div class="card card-{color}">
  <div class="card-label">{label}</div>
  <div class="card-value" style="font-size:{font_size};word-break:break-word;overflow-wrap:break-word;">{val}</div>
</div>
""",
        unsafe_allow_html=True,
    )


# Old rule-based copilot removed — Groq LLM used via copilot_service.py



state = read_json(DASHBOARD_STATE_PATH, {})
rec = read_json(RECOMMENDATION_CARD_PATH, {})
events = read_jsonl(AGENT_ACTIVITY_PATH, 100)
portfolio_state = read_json(PORTFOLIO_STATE_PATH, {})
runner_status = read_json(RUNNER_STATUS_PATH, {})
provider_status = read_json(PROVIDER_STATUS_PATH, {})
infra = read_json(INFRA_STATUS_PATH, {})
agent_health = read_json(AGENT_HEALTH_PATH, {})


status = state.get("status", {})
mc = state.get("mission_control", {})
markets = state.get("live_markets", [])
risk = state.get("risk_regime", {})
digital = state.get("digital_twin", {})
health = state.get("system_health", {})
# Override with fresher infrastructure status if available
if infra:
    _redis_status = infra.get("redis", {}).get("status", health.get("redis_status", "unknown"))
    _db_status = infra.get("timescale", {}).get("status", health.get("database_status", "unknown"))
    health = {**health, "redis_status": _redis_status, "database_status": _db_status}
portfolio = state.get("portfolio_directive", {})
provider_summary = provider_status.get("summary", {})
providers = provider_status.get("providers", {})


with st.sidebar:
    st.markdown("## AURUM Controls")
    auto = st.checkbox("Auto-refresh", value=True)
    interval = st.slider("Refresh interval", 10, 120, 30)
    st.divider()

    # Scheduler status
    _sched_path = MISSION_DIR / "scheduler_status.json"
    _sched = read_json(_sched_path, {})
    _runner = runner_status.get("runner_status", "unknown")
    _cycles = runner_status.get("cycle_count", 0)
    _last = status.get("last_refresh_time", "unknown")
    if isinstance(_last, str) and len(_last) >= 19:
        _last = _last[11:19] + " UTC"

    _runner_color = "🟢" if _runner == "idle_after_success" else "🟡" if _runner == "running" else "🔴"
    st.markdown(f"**{_runner_color} Scheduler**")
    st.caption(f"Status: {_runner}")
    st.caption(f"Cycles run: {_cycles}")
    st.caption(f"Last cycle: {_last}")

    st.divider()

    # Data freshness indicator
    _last_refresh = status.get("last_refresh_time", "")
    if _last_refresh:
        try:
            from datetime import datetime, timezone
            _dt = datetime.fromisoformat(_last_refresh.replace("Z", "+00:00"))
            _age_mins = (datetime.now(timezone.utc) - _dt).total_seconds() / 60
            if _age_mins < 6:
                _fresh_icon = "🟢"
                _fresh_label = f"Fresh ({int(_age_mins)}m ago)"
            elif _age_mins < 15:
                _fresh_icon = "🟡"
                _fresh_label = f"Aging ({int(_age_mins)}m ago)"
            else:
                _fresh_icon = "🔴"
                _fresh_label = f"Stale ({int(_age_mins)}m ago)"
            st.markdown(f"**{_fresh_icon} Data: {_fresh_label}**")
        except Exception:
            pass

    st.write("Dashboard state")
    st.code(health.get("dashboard_state_status", "unknown"))

# cycle count removed from header


# Institutional header
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
""", unsafe_allow_html=True)

b1, b2 = st.columns([1, 3])

with b1:
    if st.button("Run Mission Control Cycle Now"):
        with st.spinner("Running AURUM Mission Control cycle..."):
            run_mission_control_cycle(cycle_count=1, interval=None)
        st.success("Mission Control cycle complete.")
        st.rerun()

with b2:
    if st.button("Refresh Page"):
        st.rerun()


tabs = st.tabs(
    [
        "1. Mission Control",
        "2. Live Markets",
        "3. AI Agents",
        "4. Portfolio Directive",
        "5. Risk & Regime",
        "6. Digital Twin",
        "7. Copilot",
        "8. System Health",
        "9. Agent Command Center"
    ]
)

with tabs[0]:

    # ── Row 1: Status strip ──────────────────────────────────────────────
    regime_val = str(mc.get("current_regime", "unknown")).upper()
    posture_val = str(portfolio.get("posture", "unknown")).upper()
    execution_val = str(mc.get("execution_permission", "unknown")).upper()
    confidence_val = mc.get("cio_confidence", "N/A")
    biggest_risk_val = mc.get("biggest_risk", "N/A")

    regime_color_hex = {
        "BULL": "#16a34a", "BULLISH": "#16a34a",
        "BEAR": "#dc2626", "BEARISH": "#dc2626",
        "HIGH_VOL": "#dc2626", "DEFENSIVE": "#d97706",
    }.get(regime_val, "#d97706")

    exec_color_hex = "#dc2626" if execution_val == "BLOCKED" else "#16a34a"

    # String color names for components that use the card() function
    regime_color = {
        "BULL": "green", "BULLISH": "green",
        "BEAR": "red", "BEARISH": "red",
        "HIGH_VOL": "red", "DEFENSIVE": "yellow",
    }.get(regime_val, "yellow")
    exec_color = "red" if execution_val == "BLOCKED" else "green"

    st.markdown(f"""
<div style="display:flex;gap:12px;margin-bottom:1rem;">
  <div style="flex:1;background:white;border:1px solid #e5e7eb;border-left:6px solid {regime_color_hex};
       border-radius:12px;padding:1rem;">
    <div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.06em;">Regime</div>
    <div style="font-size:1.4rem;font-weight:800;color:#111827;">{regime_val}</div>
  </div>
  <div style="flex:1;background:white;border:1px solid #e5e7eb;border-left:6px solid #3b82f6;
       border-radius:12px;padding:1rem;">
    <div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.06em;">Posture</div>
    <div style="font-size:1.4rem;font-weight:800;color:#111827;">{posture_val}</div>
  </div>
  <div style="flex:1;background:white;border:1px solid #e5e7eb;border-left:6px solid {exec_color_hex};
       border-radius:12px;padding:1rem;">
    <div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.06em;">Execution</div>
    <div style="font-size:1.4rem;font-weight:800;color:{exec_color_hex};">{execution_val}</div>
  </div>
  <div style="flex:1;background:white;border:1px solid #e5e7eb;border-left:6px solid #16a34a;
       border-radius:12px;padding:1rem;">
    <div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.06em;">CIO Confidence</div>
    <div style="font-size:1.4rem;font-weight:800;color:#111827;">{confidence_val}</div>
  </div>
  <div style="flex:1;background:white;border:1px solid #e5e7eb;border-left:6px solid #dc2626;
       border-radius:12px;padding:1rem;">
    <div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.06em;">Biggest Risk</div>
    <div style="font-size:1.1rem;font-weight:700;color:#111827;">{biggest_risk_val}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Market Ticker Strip ─────────────────────────────────────────────
    if markets:
        ticker_parts = []
        for m in markets[:8]:
            t = m.get("ticker", "")
            p = m.get("price", 0)
            fresh = m.get("freshness", "")
            dot = "🟢" if fresh == "fresh" else "🟡"
            ticker_parts.append(f"{dot} <b>{t}</b> ${p:,.2f}")
        ticker_html = "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;".join(ticker_parts)
        st.markdown(
            f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;'
            f'padding:0.6rem 1rem;font-size:0.9rem;color:#374151;margin-bottom:1rem;">'
            f'{ticker_html}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Row 2: Live Paper Portfolio ──────────────────────────────────────
    st.markdown("### Live Paper Portfolio (Alpaca)")

    _alpaca_path = ROOT / "results" / "mission_control" / "alpaca_state.json"
    if _alpaca_path.exists():
        import json as _json3
        _alpaca = _json3.loads(_alpaca_path.read_text(encoding="utf-8"))
        _acc = _alpaca.get("account", {})
        _positions = _alpaca.get("positions", [])

        _sync_time = _alpaca.get("timestamp", "unknown")[:19]
        st.caption(f"Last sync: {_sync_time} UTC  |  Source: Alpaca Paper Trading")

        _a1, _a2, _a3, _a4 = st.columns(4)
        _pval = _acc.get("portfolio_value", 0)
        _dpnl = _acc.get("daily_pnl", 0)
        _dpct = _acc.get("daily_pnl_pct", 0)
        _pnl_color = "green" if _dpnl >= 0 else "red"

        with _a1:
            card("Portfolio Value", f"${_pval:,.2f}", "blue")
        with _a2:
            card("Daily P&L", f"${_dpnl:+,.2f}", _pnl_color)
        with _a3:
            card("Daily Return", f"{_dpct:+.2f}%", _pnl_color)
        with _a4:
            card("Cash", f"${_acc.get('cash', 0):,.2f}", "yellow")

        if _positions:
            _pos_rows = []
            for _p in _positions:
                _upl = _p.get("unrealized_pl", 0)
                _pos_rows.append({
                    "Symbol": _p.get("symbol"),
                    "Price": f"${_p.get('current_price', 0):,.2f}",
                    "Market Value": f"${_p.get('market_value', 0):,.2f}",
                    "Weight": f"{_p.get('weight_pct', 0):.1f}%",
                    "Unrealized P&L": f"${_upl:+,.2f}",
                    "Return": f"{_p.get('unrealized_plpc', 0):+.2f}%",
                })
            st.dataframe(_pos_rows, use_container_width=True)
    else:
        st.warning("Alpaca state not found. Run a mission cycle first.")

    st.divider()

    # ── Row 3: Decision Trace ────────────────────────────────────────────
    st.markdown("### Agent Decision Pipeline")

    trace_steps = [
        {"stage": "Market Data", "agent": "Market Data Agent",
         "output": f"{len(markets)} assets via {provider_summary.get('active_feed', 'unknown')}",
         "color": "blue"},
        {"stage": "Regime", "agent": "Regime Agent",
         "output": regime_val, "color": regime_color},
        {"stage": "Risk", "agent": "Risk Agent",
         "output": f"CVaR {pct(risk.get('cvar'))} | DD {pct(risk.get('drawdown'))}",
         "color": "red"},
        {"stage": "CIO Directive", "agent": "CIO Agent",
         "output": mc.get("recommended_action", "N/A"), "color": "yellow"},
        {"stage": "Governance", "agent": "Governance Agent",
         "output": execution_val,
         "color": exec_color},
        {"stage": "Next Action", "agent": "Mission Control",
         "output": rec.get("next_best_action", "N/A"), "color": "green"},
    ]

    color_map = {
        "blue": "#3b82f6", "red": "#ef4444",
        "yellow": "#f59e0b", "green": "#22c55e",
    }
    pipeline_items = "".join([
        f"""<div style="flex:1;background:white;border:1px solid #e5e7eb;
            border-left:5px solid {color_map.get(step['color'], '#3b82f6')};
            border-radius:10px;padding:0.8rem;min-width:0;">
          <div style="color:#6b7280;font-size:0.68rem;text-transform:uppercase;
               letter-spacing:.05em;margin-bottom:4px;">{step['stage']}</div>
          <div style="font-size:0.95rem;font-weight:700;color:#111827;
               word-break:break-word;line-height:1.3;">{step['output']}</div>
          <div style="color:#9ca3af;font-size:0.68rem;margin-top:4px;">{step['agent']}</div>
        </div>"""
        for step in trace_steps
    ])
    st.markdown(
        f'<div style="display:flex;gap:8px;margin-bottom:0.5rem;">{pipeline_items}</div>',
        unsafe_allow_html=True
    )

    st.divider()

    # ── Row 4: Live Mission Timeline ─────────────────────────────────────
    st.markdown("### Live Mission Timeline")

    if events:
        for event in reversed(events[-8:]):
            raw_ts = event.get("timestamp", "")
            try:
                time_label = datetime.fromisoformat(
                    raw_ts.replace("Z", "+00:00")
                ).strftime("%H:%M:%S")
            except Exception:
                time_label = raw_ts

            sev = event.get("severity", "info")
            st.markdown(
                f"""<div class="timeline-item">
  <div class="timeline-time">{time_label}</div>
  <div class="{severity_class(sev)}">{sev.upper()} — <span class="timeline-agent">{event.get("agent", "Agent")}</span></div>
  <div>{event.get("message", "")}</div>
</div>""",
                unsafe_allow_html=True,
            )
    else:
        st.warning("No timeline events available.")

    st.divider()

    # ── Row 5: Agent Health + Infrastructure ─────────────────────────────
    infra_health = infra.get("overall_infrastructure_status", "unknown")
    redis_info = infra.get("redis", {})
    timescale_info = infra.get("timescale", {})

    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("#### Agent Health")
        agents = agent_health.get("agents", {})
        overall = agent_health.get("overall_agent_health", "unknown")
        pretty = {"healthy": "HEALTHY", "attention_required": "ATTENTION",
                  "degraded": "DEGRADED"}.get(overall, overall.upper())
        color = {"healthy": "green", "attention_required": "yellow",
                 "degraded": "red"}.get(overall, "yellow")

        ah1, ah2, ah3 = st.columns(3)
        with ah1:
            card("Health", pretty, color)
        with ah2:
            card("Active", agent_health.get("active_agents", 0), "green")
        with ah3:
            card("Attention", agent_health.get("attention_agents", 0), "red")

        agent_rows = []
        for name, info in agents.items():
            agent_rows.append({
                "Agent": name,
                "Status": str(info.get("status", "unknown")).upper(),
                "Severity": str(info.get("last_severity", "unknown")).upper(),
                "Last Message": info.get("last_message", "N/A")[:60],
            })
        if agent_rows:
            st.dataframe(agent_rows, use_container_width=True)

    with right_col:
        st.markdown("#### Infrastructure")
        redis_color = "green" if redis_info.get("status") == "connected" else "yellow"
        ts_status = timescale_info.get("status", "unknown")
        ts_color = "green" if ts_status == "connected" else "yellow"

        _redis_st = redis_info.get("status", "unknown")
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
""", unsafe_allow_html=True)

        runner_st = runner_status.get("runner_status", "unknown")
        runner_color = "green" if runner_st == "idle_after_success" else "yellow"
        cycle_count_val = runner_status.get("cycle_count", 0)

        r1, r2 = st.columns(2)
        with r1:
            card("Runner", runner_st, runner_color)
        with r2:
            card("Cycles Run", cycle_count_val, "blue")


with tabs[1]:
    st.subheader("Live Markets")
    active_feed = provider_summary.get("active_feed", "unknown")
    production_ready = ", ".join(provider_summary.get("production_ready", []))
    available_interfaces = ", ".join(provider_summary.get("available_interfaces", []))

    st.info(
        f"Active market feed: {active_feed} | "
        f"Available provider interfaces: {available_interfaces} | "
        f"Production ready: {production_ready}"
    )

    with st.expander("Provider Status"):
        st.json(providers)

    if markets:
        cols = st.columns(4)
        for i, m in enumerate(markets):
            with cols[i % 4]:
                card(m.get("ticker"), m.get("price"), "blue")

        st.markdown("### Market Table")
        st.dataframe(markets, use_container_width=True)
    else:
        st.warning("No live market data found.")

with tabs[2]:
    st.subheader("Live Agent Timeline")

    if events:
        for event in reversed(events[-30:]):
            raw_ts = event.get("timestamp", "")
            try:
                time_label = datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).strftime("%H:%M:%S")
            except Exception:
                time_label = raw_ts

            sev = event.get("severity", "info")
            st.markdown(
                f"""
<div class="timeline-item">
  <div class="timeline-time">{time_label}</div>
  <div class="{severity_class(sev)}">{sev.upper()} — <span class="timeline-agent">{event.get("agent", "Agent")}</span></div>
  <div>{event.get("message", "")}</div>
</div>
""",
                unsafe_allow_html=True,
            )
    else:
        st.warning("No agent activity found.")

    
    st.markdown("### Live Agent Activity Stream")

    if events:
        latest_events = list(reversed(events[-25:]))

        for event in latest_events:
            sev = str(event.get("severity", "info")).lower()
            color = {
                "success": "green",
                "info": "blue",
                "warning": "yellow",
                "critical": "red",
                "error": "red",
            }.get(sev, "blue")

            raw_ts = event.get("timestamp", "")
            try:
                time_label = datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).strftime("%H:%M:%S")
            except Exception:
                time_label = raw_ts

            st.markdown(
                f"""
    <div class="card card-{color}" style="margin-bottom:.45rem; min-height:80px;">
    <div class="card-label">{time_label} · {event.get("agent", "Agent")} · {sev.upper()}</div>
    <div style="font-size:.95rem;font-weight:600;">{event.get("event_type", "event")}</div>
    <div style="font-size:.85rem;color:#374151;">{event.get("message", "")}</div>
    </div>
    """,
                unsafe_allow_html=True,
            )
    else:
        st.warning("No live agent activity available.")


with tabs[3]:
    st.subheader("Portfolio Directive")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Posture", str(portfolio.get("posture", "unknown")).upper(), "blue")
    with c2:
        card("Action", portfolio.get("recommended_action", "N/A"), "yellow")
    with c3:
        color = "red" if portfolio.get("execution_permission") == "blocked" else "green"
        card("Permission", portfolio.get("execution_permission", "unknown"), color)
    with c4:
        card("Confidence", portfolio.get("confidence", "N/A"), "green")

    st.markdown("### Reasoning")
    for reason in rec.get("top_reasons", []):
        st.write(f"• {reason}")

    with st.expander("Raw Portfolio Directive"):
        st.json(portfolio)


with tabs[4]:
    st.subheader("Risk & Regime")

    risk_score = risk.get("risk_score")
    try:
        score = float(risk_score)
    except Exception:
        score = None

    if score is None:
        risk_level = "UNKNOWN"
        risk_color = "blue"
    elif score < 35:
        risk_level = "LOW"
        risk_color = "green"
    elif score < 70:
        risk_level = "MEDIUM"
        risk_color = "yellow"
    else:
        risk_level = "HIGH"
        risk_color = "red"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Regime", str(risk.get("regime", "unknown")).upper(), "yellow")
    with c2:
        card("Risk Score", f"{score:.0f} / 100" if score is not None else "N/A", risk_color)
    with c3:
        card("Risk Level", risk_level, risk_color)
    with c4:
        card("CVaR", pct(risk.get("cvar")), "red")

    d1, d2 = st.columns(2)
    with d1:
        card("Drawdown", pct(risk.get("drawdown")), "red")
    with d2:
        card("Execution Permission", mc.get("execution_permission", "unknown"), "red")

    st.progress(min(int(score or 0), 100) / 100)

    st.markdown("### Anomalies")
    anomalies = risk.get("anomalies", [])
    if anomalies:
        st.warning(f"{len(anomalies)} active anomaly alert(s).")
        st.json(anomalies)
    else:
        st.success("No active anomaly alerts detected.")

    with st.expander("Raw Risk State"):
        st.json(risk)



with tabs[5]:
    st.subheader("Digital Twin & Backtest")

    # --- Backtest Equity Curve ---
    st.markdown("### Regime-Filtered CVaR Backtest (2018-2025)")
    st.caption("Walk-forward backtest | No lookahead bias | 252-day training window | Rebalance every 21 days")

    backtest_path = ROOT / "results" / "backtest" / "regime_cvar_backtest_results.json"
    if backtest_path.exists():
        import json as _json
        bt = _json.loads(backtest_path.read_text(encoding="utf-8"))
        curves = bt.get("equity_curves", [])
        metrics = bt.get("metrics", {})

        if curves:
            # Metrics summary
            m1, m2, m3, m4 = st.columns(4)
            spy_m = metrics.get("spy", {})
            cvar_m = metrics.get("regime_cvar", {})
            eq_m = metrics.get("equal_weight", {})

            with m1:
                card("SPY Sharpe", spy_m.get("sharpe_ratio", "N/A"), "blue")
            with m2:
                card("Regime CVaR Sharpe", cvar_m.get("sharpe_ratio", "N/A"), "yellow")
            with m3:
                card("SPY Max DD", f"{spy_m.get('max_drawdown_pct', 0)}%", "red")
            with m4:
                card("CVaR Max DD", f"{cvar_m.get('max_drawdown_pct', 0)}%", "green")

            st.markdown("")

            # Build chart dataframe
            chart_data = pd.DataFrame(curves)
            chart_data["date"] = pd.to_datetime(chart_data["date"])
            chart_data = chart_data.set_index("date")

            # Convert to % return for readability
            chart_data["SPY Buy & Hold"] = (chart_data["spy"] - 1) * 100
            chart_data["Equal Weight"] = (chart_data["equal_weight"] - 1) * 100
            chart_data["Regime CVaR"] = (chart_data["regime_cvar"] - 1) * 100

            st.line_chart(
                chart_data[["SPY Buy & Hold", "Equal Weight", "Regime CVaR"]],
                use_container_width=True,
            )

            st.caption("Y-axis: Cumulative return (%) from $1 starting value | Strategy trades return for risk reduction")

            # Metrics table
            st.markdown("### Strategy Comparison")
            comparison = []
            for name, key in [("SPY Buy & Hold", "spy"), ("Equal Weight", "equal_weight"), ("Regime CVaR", "regime_cvar")]:
                m = metrics.get(key, {})
                comparison.append({
                    "Strategy": name,
                    "Annual Return": f"{m.get('annual_return_pct', 0)}%",
                    "Volatility": f"{m.get('annual_volatility_pct', 0)}%",
                    "Sharpe": m.get("sharpe_ratio", 0),
                    "Max Drawdown": f"{m.get('max_drawdown_pct', 0)}%",
                    "CVaR 95%": f"{m.get('cvar_95_pct', 0)}%",
                })
            st.dataframe(comparison, use_container_width=True)

        else:
            st.warning("No equity curve data found. Run the backtest first.")
            if st.button("Run Backtest Now"):
                with st.spinner("Running backtest (1-2 minutes)..."):
                    import subprocess as _sp
                    _sp.run(["python", "-m", "src.backtest.regime_cvar_backtest"], cwd=str(ROOT))
                st.success("Backtest complete. Refresh the page.")
                st.rerun()
    else:
        st.warning("Backtest results not found.")
        if st.button("Run Backtest Now"):
            with st.spinner("Running backtest (1-2 minutes)..."):
                import subprocess as _sp
                _sp.run(["python", "-m", "src.backtest.regime_cvar_backtest"], cwd=str(ROOT))
            st.success("Backtest complete.")
            st.rerun()

    st.divider()
    st.markdown("### Digital Twin Simulation")

    monte = digital.get("monte_carlo_result", {})
    stress = digital.get("stress_test_result", {})
    contagion = digital.get("contagion_risk", {})

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Overall Status", digital.get("overall_status", "N/A"), "yellow")
    with c2:
        card("Worst Scenario", digital.get("worst_scenario", "N/A"), "red")
    with c3:
        card("Worst Return", pct(digital.get("worst_scenario_return")), "red")
    with c4:
        card("Scenario Name", digital.get("worst_scenario_name", "N/A"), "yellow")

    st.markdown("### Monte Carlo Lab")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        card("Expected Return", pct(monte.get("expected_return")), "green")
    with m2:
        card("Expected Volatility", pct(monte.get("expected_volatility")), "blue")
    with m3:
        card("VaR 95", pct(monte.get("var95")), "red")
    with m4:
        card("CVaR 95", pct(monte.get("cvar95")), "red")
    with m5:
        card("Survival", monte.get("survival", "N/A"), "green")

    st.markdown("### Stress Test")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        card("Scenario", stress.get("scenario_id", "N/A"), "red")
    with s2:
        card("Severity", stress.get("severity", "N/A"), "red")
    with s3:
        card("Portfolio Impact", pct(stress.get("portfolio_impact")), "red")
    with s4:
        card("Impacted Assets", stress.get("impacted_assets", "N/A"), "yellow")

    st.info(f"Governance Action: {stress.get('governance_action', 'N/A')}")

    st.markdown("### Contagion Engine")
    g1, g2, g3 = st.columns(3)
    with g1:
        card("Source Asset", contagion.get("source_asset", "N/A"), "red")
    with g2:
        card("Portfolio Impact", pct(contagion.get("portfolio_impact")), "red")
    with g3:
        card("Most Impacted Asset", contagion.get("most_impacted_asset", "N/A"), "yellow")

    with st.expander("Raw Digital Twin State"):
        st.json(digital)



with tabs[6]:
    st.subheader("AURUM Copilot")

    question = st.text_input(
        "Ask AURUM...",
        value="Why is execution blocked?",
        key="copilot_question_input",
    )

    quick_questions = [
        "What is the current AURUM status?",
        "Is the scheduler running?",
        "Which agent needs attention?",
        "Is Redis connected?",
        "What is the active market feed?",
        "Why are we defensive?",
        "Can we execute?",
        "What is the portfolio P&L?",
        "What is the worst digital twin scenario?",
    ]

    selected_question = st.selectbox(
        "Quick questions",
        quick_questions,
        key="copilot_quick_question",
    )

    c1, c2 = st.columns(2)

    with c1:
        ask_clicked = st.button("Ask Copilot", key="ask_copilot_button")

    with c2:
        quick_clicked = st.button("Ask Selected Question", key="ask_selected_copilot_button")

    if ask_clicked or quick_clicked:
        final_question = selected_question if quick_clicked else question

        with st.spinner("AURUM Copilot is thinking..."):
            context = load_context()
            response = answer_question(final_question, context)
            st.session_state["copilot_response"] = response

    if "copilot_response" in st.session_state:
        r = st.session_state["copilot_response"]
        st.markdown("### Answer")
        source = r.get("source", "unknown")
        model = r.get("model", "unknown")
        st.caption(f"Powered by: {model} ({source})")
        st.info(r.get("answer", "No answer available."))

        points = r.get("supporting_points", [])
        if points:
            st.markdown("### Supporting Points")
            for point in points:
                st.markdown(f"- {point}")

        with st.expander("Raw Response"):
            st.json(r)
    else:
        latest_copilot = read_json(COPILOT_RESPONSE_PATH, {})
        if latest_copilot:
            st.markdown("### Answer")
            source = latest_copilot.get("source", "unknown")
            model = latest_copilot.get("model", "unknown")
            if source not in ("unknown", "NOT FOUND", "rule_based"):
                st.caption(f"Powered by: {model} ({source})")
            st.info(latest_copilot.get("answer", "No answer available."))
            points = latest_copilot.get("supporting_points", [])
            if points:
                st.markdown("### Supporting Points")
                for point in points:
                    st.markdown(f"- {point}")
        else:
            st.warning("No copilot response available yet.")

with tabs[7]:
    st.subheader("System Health")

    c1, c2, c3 = st.columns(3)
    with c1:
        card("Last Refresh", status.get("last_refresh_time", "unknown"), "blue")
    with c2:
        card("Data Freshness", health.get("data_freshness", "unknown"), "green")
    with c3:
        card("Dashboard State", health.get("dashboard_state_status", "unknown"), "green")

    c4, c5, c6 = st.columns(3)
    with c4:
        card("Redis", health.get("redis_status", "unknown"), "yellow")
    with c5:
        card("Database", health.get("database_status", "unknown"), "yellow")
    with c6:
        card("AI Artifacts", health.get("ai_artifacts_status", "unknown"), "green")

    with st.expander("Raw Dashboard State"):
        st.json(state)

    with st.expander("Raw Recommendation Card"):
        st.json(rec)

with tabs[8]:

    st.subheader("Agent Command Center")

    if st.button("Start Scheduler", key="start_scheduler_button"):
        subprocess.Popen(
            ["python", "-m", "src.mission_control.autonomous_scheduler"],
            cwd=str(ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
        )
        st.success("Autonomous scheduler started in a separate process.")
        st.rerun()

    if st.button("Stop Scheduler", key="stop_scheduler_button"):
        st.warning("Scheduler stop support coming next.")

    col1, col2 = st.columns(2)

    with col1:

        if st.button("Run Market Data Agent"):
            os.system(
                "python -m src.mission_control.live_refresh_worker"
            )
            st.success("Market Data Agent completed.")

        if st.button("Run Regime Agent"):
            os.system(
                "python -m src.regimes.hmm_regime_engine_clean"
            )
            st.success("Regime Agent completed.")

        if st.button("Run Risk Agent"):
            os.system(
                "python -m src.mission_control.agent_health_builder"
            )
            st.success("Risk Agent completed.")

    with col2:

        if st.button("Run CIO Agent"):
            os.system(
                "python -m src.cio.chief_investment_officer_agent"
            )
            st.success("CIO Agent completed.")

        if st.button("Run Governance Agent"):
            os.system(
                "python -m src.governance.execution_governance_engine"
            )
            st.success("Governance Agent completed.")

        if st.button("Run Full Mission Cycle"):
            os.system(
                "python -m src.mission_control.run_aurum_mission_control --once"
            )
            st.success("Mission Control cycle completed.")

if auto:
    time.sleep(interval)

    with st.spinner("Auto-running AURUM Mission Control cycle..."):
        run_mission_control_cycle(cycle_count=1, interval=interval)

    st.rerun()
