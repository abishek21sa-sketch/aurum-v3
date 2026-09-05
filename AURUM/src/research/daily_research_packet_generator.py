from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class DailyResearchPacketGenerator:
    """
    AURUM Daily Research Packet Generator

    Converts the Research Desk Orchestrator output into:

    1. daily_research_packet.json
    2. daily_research_packet.txt
    """

    def __init__(self) -> None:
        self.research_dir = Path("results/research")
        self.research_dir.mkdir(parents=True, exist_ok=True)

        self.orchestrator_path = (
            self.research_dir / "research_desk_orchestration.json"
        )

        self.output_json = (
            self.research_dir / "daily_research_packet.json"
        )

        self.output_txt = (
            self.research_dir / "daily_research_packet.txt"
        )

    def generate(self) -> Dict[str, Any]:
        orchestration = self._load_orchestration()

        synthesis = orchestration.get("synthesis", {})
        agents = orchestration.get("agents", {})

        packet = {
            "platform": "AURUM",
            "artifact": "daily_research_packet",
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "executive_summary": self._build_executive_summary(
                synthesis
            ),
            "investment_committee_view": synthesis.get(
                "investment_committee_view",
                "Unavailable",
            ),
            "recommended_posture": synthesis.get(
                "recommended_posture",
                "unknown",
            ),
            "highest_priority_risk": synthesis.get(
                "highest_priority_risk",
                "unknown",
            ),
            "research_desk_confidence": synthesis.get(
                "research_desk_confidence",
                0.0,
            ),
            "key_scores": synthesis.get(
                "key_scores",
                {},
            ),
            "agent_headlines": synthesis.get(
                "agent_headlines",
                {},
            ),
            "specialist_analyst_views": self._extract_agent_views(
                agents
            ),
        }

        self._save_json(packet)
        self._save_text(packet)

        return packet

    def _build_executive_summary(
        self,
        synthesis: Dict[str, Any],
    ) -> str:
        market_view = synthesis.get(
            "overall_market_view",
            "Unavailable",
        )

        posture = synthesis.get(
            "recommended_posture",
            "unknown",
        )

        risk = synthesis.get(
            "highest_priority_risk",
            "unknown",
        )

        confidence = synthesis.get(
            "research_desk_confidence",
            0.0,
        )

        return (
            f"{market_view} "
            f"The research desk recommends posture "
            f"'{posture}'. "
            f"Highest priority risk is '{risk}'. "
            f"Research desk confidence is "
            f"{round(float(confidence), 4)}."
        )

    def _extract_agent_views(
        self,
        agents: Dict[str, Any],
    ) -> Dict[str, Any]:
        views = {}

        for name, payload in agents.items():
            output = payload.get("output", {})

            views[name] = {
                "status": payload.get(
                    "status",
                    "unknown",
                ),
                "analysis": output.get(
                    "analysis",
                    {},
                ),
                "recommendations": output.get(
                    "recommendations",
                    [],
                ),
                "explanation": output.get(
                    "explanation",
                    "",
                ),
            }

        return views

    def _save_json(
        self,
        packet: Dict[str, Any],
    ) -> None:
        with self.output_json.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                packet,
                f,
                indent=2,
                default=str,
            )

    def _save_text(
        self,
        packet: Dict[str, Any],
    ) -> None:
        lines = []

        lines.append(
            "=" * 80
        )
        lines.append(
            "AURUM DAILY RESEARCH PACKET"
        )
        lines.append(
            "=" * 80
        )

        lines.append(
            f"Generated At: {packet['generated_at']}"
        )
        lines.append("")

        lines.append(
            "EXECUTIVE SUMMARY"
        )
        lines.append(
            "-" * 80
        )
        lines.append(
            packet["executive_summary"]
        )
        lines.append("")

        lines.append(
            "INVESTMENT COMMITTEE VIEW"
        )
        lines.append(
            "-" * 80
        )
        lines.append(
            packet[
                "investment_committee_view"
            ]
        )
        lines.append("")

        lines.append(
            "RECOMMENDED POSTURE"
        )
        lines.append(
            "-" * 80
        )
        lines.append(
            str(
                packet[
                    "recommended_posture"
                ]
            )
        )
        lines.append("")

        lines.append(
            "HIGHEST PRIORITY RISK"
        )
        lines.append(
            "-" * 80
        )
        lines.append(
            str(
                packet[
                    "highest_priority_risk"
                ]
            )
        )
        lines.append("")

        lines.append(
            "RESEARCH DESK CONFIDENCE"
        )
        lines.append(
            "-" * 80
        )
        lines.append(
            str(
                packet[
                    "research_desk_confidence"
                ]
            )
        )
        lines.append("")

        lines.append(
            "KEY SCORES"
        )
        lines.append(
            "-" * 80
        )

        for key, value in packet[
            "key_scores"
        ].items():
            lines.append(
                f"{key:<35} {value}"
            )

        lines.append("")

        lines.append(
            "SPECIALIST ANALYST HEADLINES"
        )
        lines.append(
            "-" * 80
        )

        for key, value in packet[
            "agent_headlines"
        ].items():
            lines.append(
                f"{key:<25} {value}"
            )

        lines.append("")
        lines.append(
            "SPECIALIST ANALYST DETAIL"
        )
        lines.append(
            "-" * 80
        )

        for (
            agent_name,
            view,
        ) in packet[
            "specialist_analyst_views"
        ].items():

            lines.append("")
            lines.append(
                f"[{agent_name.upper()}]"
            )

            lines.append(
                f"Status: {view['status']}"
            )

            lines.append("")
            lines.append(
                "Recommendations:"
            )

            for rec in view[
                "recommendations"
            ]:
                lines.append(
                    f" - {rec}"
                )

            lines.append("")
            lines.append(
                "Explanation:"
            )

            lines.append(
                str(
                    view[
                        "explanation"
                    ]
                )
            )

        with self.output_txt.open(
            "w",
            encoding="utf-8",
        ) as f:
            f.write(
                "\n".join(lines)
            )

    def _load_orchestration(
        self,
    ) -> Dict[str, Any]:
        if not self.orchestrator_path.exists():
            raise FileNotFoundError(
                "Research desk orchestration file not found. "
                "Run research_desk_orchestrator first."
            )

        with self.orchestrator_path.open(
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)


if __name__ == "__main__":
    generator = (
        DailyResearchPacketGenerator()
    )

    packet = generator.generate()

    print(
        "=" * 80
    )
    print(
        "AURUM DAILY RESEARCH PACKET GENERATED"
    )
    print(
        "=" * 80
    )
    print(
        f"Posture: {packet['recommended_posture']}"
    )
    print(
        f"Risk: {packet['highest_priority_risk']}"
    )
    print(
        f"Confidence: {packet['research_desk_confidence']}"
    )
    print(
        f"Saved: results/research/daily_research_packet.json"
    )
    print(
        f"Saved: results/research/daily_research_packet.txt"
    )