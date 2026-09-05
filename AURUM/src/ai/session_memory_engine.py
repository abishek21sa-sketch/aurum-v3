from pathlib import Path
import json
from datetime import datetime, UTC


MEMORY_DIR = Path("results/ai")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

SESSION_MEMORY_PATH = MEMORY_DIR / "aurum_session_memory.json"


def initialize_memory():
    if not SESSION_MEMORY_PATH.exists():

        memory = {
            "created_at": datetime.now(UTC).isoformat(),
            "last_updated": datetime.now(UTC).isoformat(),
            "conversation_count": 0,
            "active_portfolio_stance": None,
            "active_risk_regime": None,
            "active_confidence_level": None,
            "conversation_history": [],
        }

        save_memory(memory)

    return load_memory()


def load_memory():
    if not SESSION_MEMORY_PATH.exists():
        return initialize_memory()

    with open(SESSION_MEMORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory: dict):
    memory["last_updated"] = datetime.now(UTC).isoformat()

    with open(SESSION_MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def add_conversation(
    query: str,
    detected_agents: list[str],
    response_summary: str,
):
    memory = load_memory()

    memory["conversation_count"] += 1

    memory["conversation_history"].append(
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "query": query,
            "agents": detected_agents,
            "response_summary": response_summary[:500],
        }
    )

    save_memory(memory)


def update_portfolio_stance(stance: str):
    memory = load_memory()

    memory["active_portfolio_stance"] = stance

    save_memory(memory)


def update_risk_regime(regime: str):
    memory = load_memory()

    memory["active_risk_regime"] = regime

    save_memory(memory)


def update_confidence_level(confidence: str):
    memory = load_memory()

    memory["active_confidence_level"] = confidence

    save_memory(memory)


def build_memory_summary():
    memory = load_memory()

    lines = []

    lines.append("=" * 90)
    lines.append("AURUM SESSION MEMORY")
    lines.append("=" * 90)

    lines.append("")
    lines.append(f"Created At: {memory['created_at']}")
    lines.append(f"Last Updated: {memory['last_updated']}")
    lines.append(f"Conversation Count: {memory['conversation_count']}")

    lines.append("")
    lines.append("ACTIVE INSTITUTIONAL STATE")
    lines.append("-" * 70)

    lines.append(
        f"Portfolio Stance: "
        f"{memory['active_portfolio_stance']}"
    )

    lines.append(
        f"Risk Regime: "
        f"{memory['active_risk_regime']}"
    )

    lines.append(
        f"Confidence Level: "
        f"{memory['active_confidence_level']}"
    )

    lines.append("")
    lines.append("RECENT CONVERSATIONS")
    lines.append("-" * 70)

    recent = memory["conversation_history"][-5:]

    if not recent:
        lines.append("No stored conversations.")
    else:
        for i, item in enumerate(recent, start=1):

            lines.append(f"[{i}] {item['timestamp']}")
            lines.append(f"Query: {item['query']}")
            lines.append(
                f"Agents: {', '.join(item['agents'])}"
            )

            lines.append(
                f"Summary: {item['response_summary']}"
            )

            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":

    initialize_memory()

    update_portfolio_stance(
        "Defensive regime-aware allocation"
    )

    update_risk_regime(
        "Moderate stress sensitivity"
    )

    update_confidence_level(
        "MODERATE CONFIDENCE"
    )

    add_conversation(
        query="What is the worst live scenario?",
        detected_agents=["scenario", "risk"],
        response_summary=(
            "Equity gap-down identified as the "
            "dominant downside vulnerability."
        ),
    )

    add_conversation(
        query="Should the committee reduce risk?",
        detected_agents=["committee", "risk"],
        response_summary=(
            "Committee debate identified ongoing "
            "tail-risk and defensive tradeoff concerns."
        ),
    )

    print(build_memory_summary())