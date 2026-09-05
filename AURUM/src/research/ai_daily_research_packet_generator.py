from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class AIDailyResearchPacketGenerator:
    """
    Generates AI-driven daily research packet from AI Research Desk output.
    """

    def __init__(self) -> None:
        self.research_dir = Path("results/research")
        self.research_dir.mkdir(parents=True, exist_ok=True)

        self.input_path = self.research_dir / "ai_research_desk.json"
        self.output_json = self.research_dir / "ai_daily_research_packet.json"
        self.output_txt = self.research_dir / "ai_daily_research_packet.txt"

    def generate(self) -> Dict[str, Any]:
        desk = self._load_desk()
        committee = desk.get("committee_analysis", {})

        packet = {
            "platform": "AURUM",
            "artifact": "ai_daily_research_packet",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "executive_summary": desk.get("executive_summary", ""),
            "committee_decision": committee.get("committee_decision", ""),
            "execution_permission": committee.get("execution_permission", ""),
            "base_case": committee.get("base_case", ""),
            "bull_case": committee.get("bull_case", ""),
            "bear_case": committee.get("bear_case", ""),
            "key_disagreements": committee.get("key_disagreements", []),
            "binding_constraint": committee.get("binding_constraint", ""),
            "risk_controls": committee.get("risk_controls", []),
            "final_recommendation": committee.get("final_recommendation", ""),
            "committee_confidence": committee.get("committee_confidence", 0.0),
            "decision_rationale": committee.get("decision_rationale", ""),
            "analyst_outputs": desk.get("analyst_outputs", {}),
        }

        self._save_json(packet)
        self._save_txt(packet)

        return packet

    def _save_json(self, packet: Dict[str, Any]) -> None:
        with self.output_json.open("w", encoding="utf-8") as f:
            json.dump(packet, f, indent=2, default=str)

    def _save_txt(self, packet: Dict[str, Any]) -> None:
        lines: List[str] = []

        lines.append("=" * 80)
        lines.append("AURUM AI DAILY RESEARCH PACKET")
        lines.append("=" * 80)
        lines.append(f"Generated At: {packet['generated_at']}")
        lines.append("")

        sections = [
            ("EXECUTIVE SUMMARY", packet["executive_summary"]),
            ("COMMITTEE DECISION", packet["committee_decision"]),
            ("EXECUTION PERMISSION", packet["execution_permission"]),
            ("BASE CASE", packet["base_case"]),
            ("BULL CASE", packet["bull_case"]),
            ("BEAR CASE", packet["bear_case"]),
            ("BINDING CONSTRAINT", packet["binding_constraint"]),
            ("FINAL RECOMMENDATION", packet["final_recommendation"]),
            ("COMMITTEE CONFIDENCE", str(packet["committee_confidence"])),
            ("DECISION RATIONALE", packet["decision_rationale"]),
        ]

        for title, content in sections:
            lines.append(title)
            lines.append("-" * 80)
            lines.append(str(content))
            lines.append("")

        lines.append("KEY DISAGREEMENTS")
        lines.append("-" * 80)
        for item in packet.get("key_disagreements", []):
            lines.append(f"- {item}")
        lines.append("")

        lines.append("RISK CONTROLS")
        lines.append("-" * 80)
        for item in packet.get("risk_controls", []):
            lines.append(f"- {item}")
        lines.append("")

        lines.append("AI ANALYST SUMMARIES")
        lines.append("-" * 80)

        for name, payload in packet.get("analyst_outputs", {}).items():
            output = payload.get("output", {})
            ai = output.get("ai_analysis", {})

            lines.append("")
            lines.append(f"[{name.upper()}]")
            lines.append(f"Status: {payload.get('status', 'unknown')}")
            lines.append(f"Thesis: {ai.get('thesis', '')}")
            lines.append(f"Recommendation: {ai.get('recommendation', '')}")
            lines.append(f"Confidence: {ai.get('confidence', '')}")

        with self.output_txt.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _load_desk(self) -> Dict[str, Any]:
        if not self.input_path.exists():
            raise FileNotFoundError(
                "AI research desk file not found. Run ai_research_desk_orchestrator first."
            )

        with self.input_path.open("r", encoding="utf-8") as f:
            return json.load(f)


if __name__ == "__main__":
    generator = AIDailyResearchPacketGenerator()
    packet = generator.generate()

    print("=" * 80)
    print("AURUM AI DAILY RESEARCH PACKET GENERATED")
    print("=" * 80)
    print(f"Decision: {packet['committee_decision']}")
    print(f"Execution Permission: {packet['execution_permission']}")
    print(f"Binding Constraint: {packet['binding_constraint']}")
    print(f"Confidence: {packet['committee_confidence']}")
    print("Saved: results/research/ai_daily_research_packet.json")
    print("Saved: results/research/ai_daily_research_packet.txt")