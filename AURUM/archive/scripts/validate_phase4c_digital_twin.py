# scripts/validate_phase4c_digital_twin.py

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import List, Tuple


class Phase4CDigitalTwinValidator:
    def __init__(self) -> None:
        self.results: List[Tuple[str, bool, str]] = []

    def record(self, name: str, passed: bool, detail: str = "") -> None:
        self.results.append((name, passed, detail))

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")

        if detail:
            print(f"       {detail}")

    def validate_imports(self) -> None:
        print("\nMODULE IMPORT CHECKS")
        print("-" * 80)

        modules = [
            "src.digital_twin.historical_replay_engine",
            "src.digital_twin.monte_carlo_lab",
            "src.digital_twin.stress_testing_framework",
            "src.digital_twin.contagion_engine",
            "src.digital_twin.regime_transition_simulator",
            "src.digital_twin.digital_twin_report_generator",
            "src.scenarios.scenario_library",
        ]

        for module in modules:
            try:
                importlib.import_module(module)
                self.record(module, True)
            except Exception as exc:
                self.record(module, False, str(exc))

    def validate_outputs(self) -> None:
        print("\nOUTPUT EXISTENCE CHECKS")
        print("-" * 80)

        paths = [
            Path("results/digital_twin/historical_replay"),
            Path("results/digital_twin/monte_carlo_lab"),
            Path("results/digital_twin/stress_testing"),
            Path("results/digital_twin/contagion_engine"),
            Path("results/digital_twin/regime_transition"),
            Path("results/digital_twin/final_report"),
            Path("results/scenarios"),
        ]

        for path in paths:
            self.record(
                str(path),
                path.exists(),
                f"path={path}",
            )

    def validate_monte_carlo(self) -> None:
        print("\nMONTE CARLO CHECKS")
        print("-" * 80)

        path = Path(
            "results/digital_twin/monte_carlo_lab/monte_carlo_summary.json"
        )

        if not path.exists():
            self.record("Monte Carlo summary", False, "missing file")
            return

        data = json.loads(path.read_text(encoding="utf-8"))

        self.record(
            "Monte Carlo simulations",
            data.get("simulations", 0) >= 1000,
            f"simulations={data.get('simulations')}",
        )

        self.record(
            "Monte Carlo survival status",
            data.get("survival_status") in {
                "ROBUST",
                "STRESSED",
                "FRAGILE",
            },
            f"status={data.get('survival_status')}",
        )

    def validate_stress_tests(self) -> None:
        print("\nSTRESS TEST CHECKS")
        print("-" * 80)

        path = Path(
            "results/digital_twin/stress_testing/stress_test_results.csv"
        )

        self.record(
            "Stress test results",
            path.exists(),
            f"path={path}",
        )

    def validate_contagion(self) -> None:
        print("\nCONTAGION CHECKS")
        print("-" * 80)

        path = Path(
            "results/digital_twin/contagion_engine/contagion_results.csv"
        )

        self.record(
            "Contagion results",
            path.exists(),
            f"path={path}",
        )

    def validate_regime(self) -> None:
        print("\nREGIME TRANSITION CHECKS")
        print("-" * 80)

        path = Path(
            "results/digital_twin/regime_transition/regime_transition_summary.json"
        )

        if not path.exists():
            self.record("Regime transition summary", False)
            return

        data = json.loads(path.read_text(encoding="utf-8"))

        self.record(
            "Current regime available",
            "current_regime" in data,
            f"current_regime={data.get('current_regime')}",
        )

        self.record(
            "Next regime available",
            "most_likely_next_regime" in data,
            f"next={data.get('most_likely_next_regime')}",
        )

    def validate_final_report(self) -> None:
        print("\nFINAL REPORT CHECKS")
        print("-" * 80)

        path = Path(
            "results/digital_twin/final_report/digital_twin_final_summary.json"
        )

        if not path.exists():
            self.record("Final report summary", False)
            return

        data = json.loads(path.read_text(encoding="utf-8"))

        self.record(
            "Digital twin status available",
            "overall_digital_twin_status" in data,
            f"status={data.get('overall_digital_twin_status')}",
        )

    def summarize(self) -> None:
        print("\n" + "=" * 80)
        print("PHASE 4C DIGITAL TWIN VALIDATION SUMMARY")
        print("=" * 80)

        passed = sum(1 for _, ok, _ in self.results if ok)
        total = len(self.results)
        failed = total - passed

        print(f"Passed: {passed}/{total}")
        print(f"Failed: {failed}/{total}")

        if failed == 0:
            print("\nPHASE 4C COMPLETE")
            print("AURUM Market Digital Twin is operational.")
        else:
            print("\nPHASE 4C NOT COMPLETE")
            print("Fix failed checks and rerun validation.")

    def run(self) -> None:
        print("=" * 80)
        print("AURUM PHASE 4C DIGITAL TWIN VALIDATION")
        print("=" * 80)

        self.validate_imports()
        self.validate_outputs()
        self.validate_monte_carlo()
        self.validate_stress_tests()
        self.validate_contagion()
        self.validate_regime()
        self.validate_final_report()
        self.summarize()


def main() -> None:
    validator = Phase4CDigitalTwinValidator()
    validator.run()


if __name__ == "__main__":
    main()