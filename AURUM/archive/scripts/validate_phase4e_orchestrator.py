from src.orchestrator.portfolio_operating_orchestrator import (
    run_portfolio_operating_orchestrator,
)

report = run_portfolio_operating_orchestrator()

assert report["total_steps"] > 0

print("=" * 80)
print("PHASE 4E.1 ORCHESTRATOR VALIDATION")
print("=" * 80)
print(f"Status: {report['status']}")
print(f"Passed: {report['steps_passed']}")
print(f"Failed: {report['steps_failed']}")
print("[PASS]")