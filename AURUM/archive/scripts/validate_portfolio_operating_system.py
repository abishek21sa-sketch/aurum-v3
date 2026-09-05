# scripts/validate_portfolio_operating_system.py

import importlib
import json
import subprocess
import sys
from pathlib import Path


REQUIRED_MODULES = [
    "src.portfolio.portfolio_audit_trail",
    "src.portfolio.portfolio_state_manager",
    "src.portfolio.portfolio_operating_report",
    "src.portfolio.portfolio_decision_orchestrator",
    "src.portfolio.governance_execution_gate",
    "src.portfolio.end_to_end_portfolio_pipeline",
]

REQUIRED_OUTPUTS = {
    "audit_log": "results/portfolio_audit/portfolio_audit_log.jsonl",
    "institutional_state": "results/portfolio_state/institutional_portfolio_state.json",
    "operating_report_json": "results/portfolio/portfolio_operating_report.json",
    "operating_report_txt": "results/portfolio/portfolio_operating_report.txt",
    "decision_orchestration": "results/portfolio/portfolio_decision_orchestration.json",
    "governance_execution_gate": "results/portfolio/governance_execution_decision.json",
    "end_to_end_pipeline": "results/portfolio/end_to_end_portfolio_pipeline_summary.json",
}


def check_module_imports():
    results = {}

    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
            results[module] = "PASS"
        except Exception as exc:
            results[module] = f"FAIL: {exc}"

    return results


def run_pipeline():
    result = subprocess.run(
        [sys.executable, "-m", "src.portfolio.end_to_end_portfolio_pipeline"],
        capture_output=True,
        text=True,
    )

    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "return_code": result.returncode,
        "stdout_tail": result.stdout[-3000:],
        "stderr_tail": result.stderr[-3000:],
    }


def check_outputs():
    return {
        name: {
            "path": path,
            "exists": Path(path).exists(),
        }
        for name, path in REQUIRED_OUTPUTS.items()
    }


def load_json(path):
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def validate_semantics():
    gate = load_json("results/portfolio/governance_execution_decision.json")
    pipeline = load_json("results/portfolio/end_to_end_portfolio_pipeline_summary.json")
    orchestration = load_json("results/portfolio/portfolio_decision_orchestration.json")
    operating_report = load_json("results/portfolio/portfolio_operating_report.json")

    checks = {
        "governance_gate_has_execution_status": bool(gate.get("execution_status")),
        "pipeline_has_execution_status": bool(pipeline.get("execution_status")),
        "orchestrator_ready_flag_exists": "portfolio_operating_system_ready"
        in orchestration.get("institutional_status", {}),
        "operating_report_has_monitoring": bool(operating_report.get("monitoring")),
        "operating_report_has_governance": bool(operating_report.get("governance")),
        "operating_report_has_execution": bool(operating_report.get("execution")),
    }

    return checks


def main():
    print("=" * 80)
    print("AURUM PORTFOLIO OPERATING SYSTEM VALIDATION")
    print("=" * 80)

    print("\nMODULE IMPORT CHECKS")
    print("-" * 80)
    module_results = check_module_imports()
    for module, status in module_results.items():
        print(f"[{status if status == 'PASS' else 'FAIL'}] {module}")
        if status != "PASS":
            print(f"       {status}")

    print("\nPIPELINE EXECUTION CHECK")
    print("-" * 80)
    pipeline_result = run_pipeline()
    print(f"[{pipeline_result['status']}] end-to-end portfolio pipeline")
    if pipeline_result["status"] != "PASS":
        print(pipeline_result["stderr_tail"])

    print("\nOUTPUT EXISTENCE CHECKS")
    print("-" * 80)
    output_results = check_outputs()
    for name, item in output_results.items():
        status = "PASS" if item["exists"] else "FAIL"
        print(f"[{status}] {name}")
        print(f"       path: {item['path']}")

    print("\nSEMANTIC CHECKS")
    print("-" * 80)
    semantic_results = validate_semantics()
    for name, passed in semantic_results.items():
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")

    all_modules_passed = all(status == "PASS" for status in module_results.values())
    all_outputs_exist = all(item["exists"] for item in output_results.values())
    all_semantics_passed = all(semantic_results.values())
    pipeline_passed = pipeline_result["status"] == "PASS"

    final_pass = (
        all_modules_passed
        and pipeline_passed
        and all_outputs_exist
        and all_semantics_passed
    )

    validation_summary = {
        "validation_name": "AURUM_PORTFOLIO_OPERATING_SYSTEM_VALIDATION",
        "final_status": "PASS" if final_pass else "FAIL",
        "module_results": module_results,
        "pipeline_result": pipeline_result,
        "output_results": output_results,
        "semantic_results": semantic_results,
    }

    summary_path = Path("results/portfolio/portfolio_operating_system_validation.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(validation_summary, indent=2), encoding="utf-8")

    print("\nFINAL VERDICT")
    print("-" * 80)
    print("PASS" if final_pass else "FAIL")
    print(f"Validation Summary Saved: {summary_path}")

    if final_pass:
        print("\nPHASE 3H COMPLETE")
        print("AURUM now has a governance-aware institutional portfolio operating system.")


if __name__ == "__main__":
    main()