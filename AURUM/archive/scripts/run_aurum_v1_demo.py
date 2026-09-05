"""
AURUM V1 DEMO RUNNER

Single-command demonstration of the AURUM platform.

Execution Flow

1. Live Market Refresh
2. Feature + Regime Generation
3. Institutional Anomaly Detection
4. CVaR LP Optimization
5. Portfolio OS
6. AI Research Firm
7. Dashboard State Export
8. Demo Summary

Usage
-----
python -m scripts.run_aurum_v1_demo
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, UTC
from pathlib import Path
import sys


OUTPUT_DIR = Path("reports/aurum_v1_demo")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_step(name: str, command: list[str]) -> dict:
    """Execute a module and capture result."""

    print("=" * 80)
    print(f"RUNNING: {name}")
    print("=" * 80)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

        print("[PASS]")

        return {
            "step": name,
            "status": "success",
            "stdout": result.stdout[-5000:],
        }

    except subprocess.CalledProcessError as exc:

        print("[FAIL]")

        return {
            "step": name,
            "status": "failed",
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }


def main():

    print("=" * 80)
    print("AURUM V1 DEMO")
    print("=" * 80)

    steps = [

        (
            "Live Market Refresh",
            [
                sys.executable,
                "-m",
                "scripts.generate_live_market_snapshot",
            ],
        ),

        (
            "Regime Intelligence",
            [
                sys.executable,
                "-m",
                "src.regimes.hmm_regime_engine_clean",
            ],
        ),

        (
            "Institutional Anomaly Detector",
            [
                sys.executable,
                "-m",
                "src.intelligence.institutional_anomaly_detector",
            ],
        ),

        (
            "CVaR LP Optimizer",
            [
                sys.executable,
                "-m",
                "src.optimization.cvar_lp_optimizer",
            ],
        ),

        (
            "Portfolio Operating System",
            [
                sys.executable,
                "-m",
                "src.portfolio_os.portfolio_operating_system",
            ],
        ),

        (
            "AI Research Firm",
            [
                sys.executable,
                "-m",
                "src.research_firm.ai_research_firm_mode",
            ],
        ),
    ]

    results = []

    for name, command in steps:
        results.append(run_step(name, command))

    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "steps": results,
        "successful_steps": sum(
            r["status"] == "success"
            for r in results
        ),
        "total_steps": len(results),
    }

    summary_path = OUTPUT_DIR / "demo_run_summary.json"

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    report_path = OUTPUT_DIR / "demo_console_report.txt"

    with open(report_path, "w", encoding="utf-8") as f:

        f.write("AURUM V1 DEMO REPORT\n")
        f.write("=" * 80 + "\n\n")

        for result in results:

            f.write(
                f"{result['step']} : "
                f"{result['status'].upper()}\n"
            )

    print()
    print("=" * 80)
    print("AURUM V1 DEMO COMPLETE")
    print("=" * 80)
    print(f"Summary Saved: {summary_path}")
    print(f"Report Saved : {report_path}")


if __name__ == "__main__":
    main()
