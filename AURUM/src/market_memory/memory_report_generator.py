from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.market_memory.memory_retriever import InstitutionalMemoryRetriever
from src.market_memory.memory_similarity_engine import MarketMemorySimilarityEngine


MEMORY_REPORT_JSON = Path("results/memory/institutional_memory_report.json")
MEMORY_REPORT_TXT = Path("results/memory/institutional_memory_report.txt")


class InstitutionalMemoryReportGenerator:
    """
    Generates institutional memory report for AURUM.
    """

    def __init__(self) -> None:
        self.retriever = InstitutionalMemoryRetriever()
        self.similarity_engine = MarketMemorySimilarityEngine()

    def generate_report(
        self,
        current_state: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        current_state = current_state or {
            "volatility": 0.0836,
            "stress_score": 0.40,
            "breadth": 0.40,
            "projected_var95": 0.1300,
            "projected_drawdown": -0.0641,
        }

        summary = self.retriever.summary()
        resemblance = self.similarity_engine.current_market_resemblance_report(
            current_state=current_state,
            limit=5,
        )

        best_allocations = self.retriever.get_best_allocations(metric="sharpe", limit=3)
        worst_allocations = self.retriever.get_worst_allocations(metric="max_drawdown", limit=3)

        report = {
            "report_name": "AURUM Institutional Memory Report",
            "memory_summary": {
                "total_records": summary["total_records"],
                "by_type": summary["by_type"],
                "by_regime": summary["by_regime"],
            },
            "current_state": current_state,
            "historical_resemblance": resemblance,
            "best_allocations": best_allocations,
            "worst_allocations": worst_allocations,
            "institutional_interpretation": self._interpret(resemblance),
        }

        MEMORY_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)

        with MEMORY_REPORT_JSON.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        with MEMORY_REPORT_TXT.open("w", encoding="utf-8") as f:
            f.write(self._to_text(report))

        return report

    def _interpret(self, resemblance: Dict[str, Any]) -> Dict[str, Any]:
        best = resemblance.get("best_match")

        if not best:
            return {
                "seen_before": False,
                "message": "No comparable institutional memory found.",
            }

        similarity = float(best.get("similarity_percent", 0))

        if similarity >= 85:
            confidence_label = "HIGH"
        elif similarity >= 70:
            confidence_label = "MODERATE"
        else:
            confidence_label = "LOW"

        return {
            "seen_before": True,
            "closest_memory": best.get("title"),
            "closest_regime": best.get("regime"),
            "similarity_percent": similarity,
            "confidence_label": confidence_label,
            "message": (
                f"Current market resembles '{best.get('title')}' "
                f"with {similarity}% similarity."
            ),
        }

    def _allocation_lines(self, records: List[Dict[str, Any]]) -> List[str]:
        lines = []

        if not records:
            return ["None"]

        for r in records:
            allocation_name = r.get("metadata", {}).get("allocation_name", r.get("title"))
            sharpe = r.get("outcome", {}).get("sharpe")
            max_dd = r.get("outcome", {}).get("max_drawdown")
            regime = r.get("regime")

            lines.append(
                f"{allocation_name} | regime={regime} | sharpe={sharpe} | max_drawdown={max_dd}"
            )

        return lines

    def _to_text(self, report: Dict[str, Any]) -> str:
        interpretation = report["institutional_interpretation"]
        resemblance = report["historical_resemblance"]
        best = resemblance.get("best_match")

        lines = []
        lines.append("=" * 80)
        lines.append("AURUM INSTITUTIONAL MEMORY REPORT")
        lines.append("=" * 80)

        lines.append("")
        lines.append("MEMORY SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Records: {report['memory_summary']['total_records']}")
        lines.append(f"By Type:       {report['memory_summary']['by_type']}")
        lines.append(f"By Regime:     {report['memory_summary']['by_regime']}")

        lines.append("")
        lines.append("HAVE WE SEEN THIS BEFORE?")
        lines.append("-" * 80)

        if best:
            lines.append(f"Closest Historical Memory: {best.get('title')}")
            lines.append(f"Regime:                    {best.get('regime')}")
            lines.append(f"Similarity:                {best.get('similarity_percent')}%")
            lines.append(f"Confidence Label:          {interpretation.get('confidence_label')}")
        else:
            lines.append("Closest Historical Memory: None")

        lines.append("")
        lines.append("BEST ALLOCATION MEMORIES")
        lines.append("-" * 80)
        lines.extend(self._allocation_lines(report["best_allocations"]))

        lines.append("")
        lines.append("WORST ALLOCATION MEMORIES")
        lines.append("-" * 80)
        lines.extend(self._allocation_lines(report["worst_allocations"]))

        lines.append("")
        lines.append("INSTITUTIONAL INTERPRETATION")
        lines.append("-" * 80)
        lines.append(interpretation.get("message", ""))

        lines.append("=" * 80)

        return "\n".join(lines)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5C MEMORY REPORT GENERATOR")
    print("=" * 80)

    generator = InstitutionalMemoryReportGenerator()
    report = generator.generate_report()

    interpretation = report["institutional_interpretation"]

    print(f"Total Records:     {report['memory_summary']['total_records']}")
    print(f"Seen Before:       {interpretation.get('seen_before')}")
    print(f"Closest Memory:    {interpretation.get('closest_memory')}")
    print(f"Similarity:        {interpretation.get('similarity_percent')}%")
    print(f"Report JSON:       {MEMORY_REPORT_JSON}")
    print(f"Report TXT:        {MEMORY_REPORT_TXT}")
    print("=" * 80)


if __name__ == "__main__":
    main()