from __future__ import annotations

import traceback
from datetime import datetime, timezone

from src.research.ai_research_desk_orchestrator import AIResearchDeskOrchestrator
from src.research.ai_daily_research_packet_generator import (
    AIDailyResearchPacketGenerator,
)


def main() -> None:
    print("=" * 80)
    print("AURUM AI RESEARCH DESK")
    print("=" * 80)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()

    try:
        print("[1/2] Running AI Research Desk Orchestrator...")
        desk = AIResearchDeskOrchestrator()
        desk_result = desk.run()

        print("[PASS] AI Research Desk Orchestrator")
        print(f"        Posture: {desk_result['recommended_posture']}")
        print(f"        Highest Risk: {desk_result['highest_priority_risk']}")
        print(f"        Confidence: {desk_result['research_confidence']}")
        print()

        print("[2/2] Generating AI Daily Research Packet...")
        generator = AIDailyResearchPacketGenerator()
        packet = generator.generate()

        print("[PASS] AI Daily Research Packet")
        print(f"        Permission: {packet['execution_permission']}")
        print(f"        Constraint: {packet['binding_constraint']}")
        print(f"        Confidence: {packet['committee_confidence']}")
        print()

        print("=" * 80)
        print("AURUM AI RESEARCH DESK COMPLETE")
        print("=" * 80)
        print("Artifacts Generated:")
        print("  results/research/ai_research_committee.json")
        print("  results/research/ai_research_desk.json")
        print("  results/research/ai_daily_research_packet.json")
        print("  results/research/ai_daily_research_packet.txt")
        print()
        print("FINAL AI COMMITTEE RECOMMENDATION")
        print("-" * 80)
        print(packet["final_recommendation"])

    except Exception as exc:
        print()
        print("[FAIL] AI Research Desk Execution Failed")
        print(f"Error: {exc}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()