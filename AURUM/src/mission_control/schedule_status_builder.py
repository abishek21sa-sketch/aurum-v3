import json
from pathlib import Path
from datetime import datetime, timezone

OUTPUT = Path(
    "results/mission_control/scheduler_status.json"
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

data = {
    "status": "manual",
    "cycles_completed": 1,
    "last_cycle": datetime.now(
        timezone.utc
    ).strftime("%H:%M:%S"),
    "next_run": "manual"
}

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        data,
        f,
        indent=2
    )

print("saved:", OUTPUT)