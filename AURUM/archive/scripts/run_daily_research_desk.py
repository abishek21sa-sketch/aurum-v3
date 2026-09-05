from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone

from src.research.research_desk_orchestrator import (
    ResearchDeskOrchestrator,
)
from src.research.daily_research_packet_generator import (
    DailyResearchPacketGenerator,
)


def main() -> None:
    print("=" * 80)
    print("AURUM DAILY RESEARCH DESK")
    print("=" * 80)
    print(
        f"Started: {datetime.now(timezone.utc).isoformat()}"
    )
    print()

    try:
        print(
            "[1/2] Running Research Desk Orchestrator..."
        )

        orchestrator = (
            ResearchDeskOrchestrator()
        )

        orchestration_result = (
            orchestrator.run()
        )

        synthesis = orchestration_result[
            "synthesis"
        ]

        print(
            "[PASS] Research Desk Orchestrator"
        )

        print(
            f"        Posture: "
            f"{synthesis['recommended_posture']}"
        )

        print(
            f"        Highest Risk: "
            f"{synthesis['highest_priority_risk']}"
        )

        print(
            f"        Confidence: "
            f"{synthesis['research_desk_confidence']}"
        )

        print()

        print(
            "[2/2] Generating Daily Research Packet..."
        )

        generator = (
            DailyResearchPacketGenerator()
        )

        packet = generator.generate()

        print(
            "[PASS] Daily Research Packet"
        )

        print(
            f"        Posture: "
            f"{packet['recommended_posture']}"
        )

        print(
            f"        Risk: "
            f"{packet['highest_priority_risk']}"
        )

        print(
            f"        Confidence: "
            f"{packet['research_desk_confidence']}"
        )

        print()
        print("=" * 80)
        print(
            "AURUM DAILY RESEARCH DESK COMPLETE"
        )
        print("=" * 80)

        print(
            "Artifacts Generated:"
        )

        print(
            "  results/research/research_desk_orchestration.json"
        )

        print(
            "  results/research/daily_research_packet.json"
        )

        print(
            "  results/research/daily_research_packet.txt"
        )

        print()

        print(
            "FINAL RECOMMENDATION"
        )

        print(
            "-" * 80
        )

        print(
            packet[
                "investment_committee_view"
            ]
        )

    except Exception as exc:
        print()
        print(
            "[FAIL] Research Desk Execution Failed"
        )

        print(
            f"Error: {exc}"
        )

        print()

        traceback.print_exc()

        raise


if __name__ == "__main__":
    main()