import json
from pathlib import Path


MEMORY_PATH = "results/ai_memory.json"


def load_memory():

    path = Path(MEMORY_PATH)

    if not path.exists():
        return {}

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def save_memory(memory: dict):

    path = Path(MEMORY_PATH)

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(memory, indent=4),
        encoding="utf-8"
    )


def update_memory(key: str, value):

    memory = load_memory()

    memory[key] = value

    save_memory(memory)


if __name__ == "__main__":

    update_memory(
        "latest_market_regime",
        "normal"
    )

    update_memory(
        "latest_risk_signal",
        "neutral"
    )

    print(load_memory())
