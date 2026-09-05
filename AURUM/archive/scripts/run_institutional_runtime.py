# scripts/run_institutional_runtime.py

import subprocess
import sys
from datetime import datetime, UTC


PIPELINE = [
    "src.runtime.aurum_runtime_orchestrator",
    "src.runtime.runtime_health_monitor",
    "src.runtime.runtime_manifest_engine",
    "src.runtime.runtime_checkpoint_engine",
    "src.runtime.runtime_governance_gate",
    "src.runtime.runtime_state_snapshot",
    "src.runtime.runtime_drift_detector",
]


def run_step(module_name: str) -> bool:
    print("\n" + "=" * 90)
    print(f"RUNNING: {module_name}")
    print("=" * 90)

    start = datetime.now(UTC)

    result = subprocess.run(
        [sys.executable, "-m", module_name],
        text=True,
    )

    end = datetime.now(UTC)

    duration = (end - start).total_seconds()

    if result.returncode == 0:
        print(f"\nSTATUS: PASS | runtime={duration:.4f}s")
        return True

    print(f"\nSTATUS: FAIL | runtime={duration:.4f}s")
    return False


def main():
    print("=" * 90)
    print("AURUM INSTITUTIONAL RUNTIME")
    print("=" * 90)

    overall_success = True

    for module in PIPELINE:
        success = run_step(module)

        if not success:
            overall_success = False
            print("\nINSTITUTIONAL RUNTIME HALTED")
            break

    print("\n" + "=" * 90)

    if overall_success:
        print("AURUM INSTITUTIONAL RUNTIME COMPLETED SUCCESSFULLY")
    else:
        print("AURUM INSTITUTIONAL RUNTIME FAILED")

    print("=" * 90)


if __name__ == "__main__":
    main()