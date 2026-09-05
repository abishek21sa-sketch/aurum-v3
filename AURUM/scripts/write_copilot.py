from pathlib import Path

code = '''"""
AURUM Copilot Service — Real LLM Edition

Uses Groq (Llama 3.3 70B) to answer questions about the live AURUM system.
Falls back to rule-based answers if Groq is unavailable.

Run:
    python -m src.mission_control.copilot_service --question "Why are we defensive?"
"""

from __future__ import annotations

import argparse
import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MISSION_DIR = ROOT / "results" / "mission_control"

DASHBOARD_STATE_PATH = MISSION_DIR / "dashboard_state.json"
RECOMMENDATION_CARD_PATH = MISSION_DIR / "recommendation_card.json"
AGENT_ACTIVITY_PATH = MISSION_DIR / "agent_activity.jsonl"
PORTFOLIO_STATE_PATH = MISSION_DIR / "portfolio_state.json"
INFRA_STATUS_PATH = MISSION_DIR / "infrastructure_status.json"
AGENT_HEALTH_PATH = MISSION_DIR / "agent_health.json"
SCHEDULER_STATUS_PATH = MISSION_DIR / "scheduler_status.json"
PROVIDER_STATUS_PATH = MISSION_DIR / "provider_status.json"
ALPACA_STATE_PATH = MISSION_DIR / "alpaca_state.json"
COPILOT_RESPONSE_PATH = MISSION_DIR / "copilot_response.json"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_jsonl(path: Path, limit: int = 20) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows[-limit:]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_context() -> dict[str, Any]:
    return {
        "dashboard_state": read_json(DASHBOARD_STATE_PATH, {}),
        "recommendation_card": read_json(RECOMMENDATION_CARD_PATH, {}),
        "agent_activity": read_jsonl(AGENT_ACTIVITY_PATH),
        "portfolio_state": read_json(PORTFOLIO_STATE_PATH, {}),
        "infrastructure_status": read_json(INFRA_STATUS_PATH, {}),
        "agent_health": read_json(AGENT_HEALTH_PATH, {}),
        "scheduler_status": read_json(SCHEDULER_STATUS_PATH, {}),
        "provider_status": read_json(PROVIDER_STATUS_PATH, {}),
        "alpaca_state": read_json(ALPACA_STATE_PATH, {}),
    }


def build_system_prompt(context: dict[str, Any]) -> str:
    """Build a tight system prompt with live AURUM state."""
    mc = context.get("dashboard_state", {}).get("mission_control", {})
    portfolio = context.get("portfolio_state", {})
    alpaca = context.get("alpaca_state", {}).get("account", {})
    rec = context.get("recommendation_card", {})
    risk = context.get("dashboard_state", {}).get("risk_regime", {})
    digital = context.get("dashboard_state", {}).get("digital_twin", {})
    markets = context.get("dashboard_state", {}).get("live_markets", [])
    agent_health = context.get("agent_health", {})

    # Build market summary
    market_lines = []
    for m in markets[:6]:
        ticker = m.get("ticker", "")
        price = m.get("price", 0)
        market_lines.append(f"{ticker}: ${price:,.2f}")
    market_summary = ", ".join(market_lines)

    # Build position summary
    alpaca_positions = context.get("alpaca_state", {}).get("positions", [])
    position_lines = []
    for p in alpaca_positions:
        position_lines.append(
            f"{p.get('symbol')}: {p.get('weight_pct')}% "
            f"(P&L: ${p.get('unrealized_pl', 0):+,.0f})"
        )
    position_summary = ", ".join(position_lines) if position_lines else "No positions"

    prompt = f"""You are AURUM, an institutional AI portfolio intelligence system.
You have access to live market data, regime detection, CVaR optimization, and a paper trading portfolio.
Answer questions concisely and professionally, like a quant analyst would.
Never make up data — only use what is provided below.

=== LIVE SYSTEM STATE ===
Timestamp: {utc_now()}

MARKET REGIME: {mc.get("current_regime", "unknown").upper()}
Portfolio Posture: {mc.get("portfolio_posture", "unknown")}
Execution Status: {mc.get("execution_permission", "unknown")}
CIO Confidence: {mc.get("cio_confidence", "N/A")}
Recommended Action: {mc.get("recommended_action", "unknown")}
Biggest Risk: {mc.get("biggest_risk", "unknown")}
Next Best Action: {rec.get("next_best_action", "unknown")}

LIVE MARKETS: {market_summary}

PAPER PORTFOLIO (Alpaca):
Portfolio Value: ${alpaca.get("portfolio_value", 0):,.2f}
Daily P&L: ${alpaca.get("daily_pnl", 0):+,.2f} ({alpaca.get("daily_pnl_pct", 0):+.2f}%)
Cash: ${alpaca.get("cash", 0):,.2f}
Positions: {position_summary}

RISK METRICS:
CVaR (95%): {risk.get("cvar", "N/A")}
Max Drawdown: {risk.get("max_drawdown", "N/A")}
Volatility: {risk.get("volatility", "N/A")}

DIGITAL TWIN:
Worst Scenario: {digital.get("worst_scenario", "N/A")}
Worst Return: {digital.get("worst_scenario_return", "N/A")}
Twin Status: {digital.get("overall_status", "N/A")}

AGENT HEALTH: {agent_health.get("overall_agent_health", "unknown")}
Active Agents: {agent_health.get("active_agents", 0)}

=== BACKTEST CONTEXT ===
Strategy: Regime-Filtered CVaR (walk-forward, 2018-2025)
Sharpe: 0.54 vs SPY 0.71
Volatility: 12.1% vs SPY 19.5%
Max Drawdown: -28.6% vs SPY -33.7%
CVaR 95%: -1.78% vs SPY -2.99%
Note: Strategy trades return for risk reduction. Designed to survive, not to chase.
"""
    return prompt


def call_groq(question: str, system_prompt: str) -> str:
    """Call Groq API and return the answer string."""
    load_env()
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return ""

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "max_tokens": 300,
        "temperature": 0.3,
    }

    try:
        r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"  [Copilot] Groq error {r.status_code}: {r.text[:200]}")
            return ""
    except Exception as e:
        print(f"  [Copilot] Groq request failed: {e}")
        return ""


def fallback_answer(question: str, context: dict[str, Any]) -> str:
    """Rule-based fallback if Groq is unavailable."""
    mc = context.get("dashboard_state", {}).get("mission_control", {})
    portfolio = context.get("portfolio_state", {})
    regime = mc.get("current_regime", "unknown")
    posture = mc.get("portfolio_posture", "unknown")
    execution = mc.get("execution_permission", "unknown")
    action = mc.get("recommended_action", "unknown")
    biggest_risk = mc.get("biggest_risk", "unknown")
    confidence = mc.get("cio_confidence", "N/A")

    return (
        f"AURUM status: regime={regime}, posture={posture}, "
        f"execution={execution}, CIO confidence={confidence}, "
        f"biggest risk={biggest_risk}, recommended action={action}. "
        f"Portfolio value: ${portfolio.get(\'portfolio_value\', 0):,.0f}, "
        f"daily P&L: ${portfolio.get(\'daily_pnl\', 0):+,.0f}."
    )


def answer_question(question: str, context: dict[str, Any]) -> dict[str, Any]:
    """Main entry point — tries Groq first, falls back to rule-based."""
    system_prompt = build_system_prompt(context)

    # Try Groq
    answer = call_groq(question, system_prompt)

    # Fallback
    if not answer:
        answer = fallback_answer(question, context)
        source = "fallback"
    else:
        source = "groq_llama3.3_70b"

    rec = context.get("recommendation_card", {})

    payload = {
        "timestamp": utc_now(),
        "question": question,
        "answer": answer,
        "source": source,
        "model": GROQ_MODEL if source != "fallback" else "rule_based",
        "supporting_points": rec.get("top_reasons", []),
        "context_used": [
            "dashboard_state", "recommendation_card", "agent_activity",
            "portfolio_state", "alpaca_state", "agent_health",
        ],
    }

    write_json(COPILOT_RESPONSE_PATH, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", default="What is the current AURUM status and why?")
    args = parser.parse_args()

    context = load_context()
    response = answer_question(args.question, context)

    print("=" * 80)
    print("AURUM COPILOT")
    print("=" * 80)
    print(f"Question: {response[\'question\']}")
    print(f"Source:   {response[\'source\']} / {response[\'model\']}")
    print("-" * 80)
    print(response["answer"])
    print("-" * 80)
    print(f"Saved: {COPILOT_RESPONSE_PATH.relative_to(ROOT)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
'''

Path("src/mission_control/copilot_service.py").write_text(code, encoding="utf-8")
print("Written.")
import py_compile
py_compile.compile("src/mission_control/copilot_service.py", doraise=True)
print("Syntax OK.")