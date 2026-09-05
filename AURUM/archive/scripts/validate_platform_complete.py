from __future__ import annotations

import subprocess
import sys


VALIDATORS = [
    "scripts.validate_core_quant",
    "scripts.validate_realtime_stack",
    "scripts.validate_portfolio_os",
    "scripts.validate_ai_research_firm",
]


def main() -> None:
    print("=" * 80)
    print("AURUM PLATFORM COMPLETE VALIDATION")
    print("=" * 80)

    passed = True

    for validator in VALIDATORS:
        print()
        print("=" * 80)
        print(f"RUNNING {validator}")
        print("=" * 80)

        result = subprocess.run(
            [sys.executable, "-m", validator],
            text=True,
        )

        if result.returncode != 0:
            passed = False
            print(f"[FAIL] {validator}")
        else:
            print(f"[PASS] {validator}")

    print()
    print("=" * 80)
    if passed:
        print("[PASS] AURUM PLATFORM COMPLETE VALIDATION PASSED")
    else:
        print("[FAIL] AURUM PLATFORM COMPLETE VALIDATION FAILED")
    print("=" * 80)


if __name__ == "__main__":
    main()