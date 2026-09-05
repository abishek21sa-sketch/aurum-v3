# src/digital_twin/live_scenario_matching_engine.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List


LIVE_STATE_PATH = Path("results/digital_twin/live_state/live_market_state.json")

HISTORICAL_REPLAY_PATH = Path(
    "results/digital_twin/historical_replay/historical_replay_results.json"
)

STRESS_TEST_PATH = Path(
    "results/digital_twin/stress_testing/stress_test_results.json"
)

OUTPUT_DIR = Path("results/digital_twin/live_scenario_matching")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ScenarioMatch:
    scenario_id: str
    scenario_type: str
    similarity_score: float
    explanation: str


@dataclass
class ScenarioMatchingResult:
    timestamp_utc: str
    live_state_label: str
    market_stress_score: float
    closest_scenario: str
    closest_scenario_type: str
    closest_similarity_score: float
    matches: List[ScenarioMatch]


class LiveScenarioMatchingEngine:
    def load_json(self, path: Path) -> Any:
        if not path.exists():
            return [] if path.suffix == ".json" else {}
        return json.loads(path.read_text(encoding="utf-8"))

    def score_historical_replay(
        self,
        live_state: Dict[str, Any],
        replay: Dict[str, Any],
    ) -> ScenarioMatch:
        stress_score = float(live_state.get("market_stress_score", 0.0))
        state_label = str(live_state.get("state_label", "unknown")).lower()

        max_drawdown = abs(float(replay.get("max_drawdown", 0.0)))
        cumulative_loss = abs(min(float(replay.get("cumulative_return", 0.0)), 0.0))

        scenario_stress = min(max_drawdown + cumulative_loss, 1.0)

        score = 1.0 - abs(stress_score - scenario_stress)
        score = max(min(score, 1.0), 0.0)

        if state_label in {"stressed", "critical"} and scenario_stress >= 0.15:
            score += 0.10

        score = round(min(score, 1.0), 4)

        explanation = (
            f"Live stress={stress_score:.2f}, "
            f"historical drawdown={max_drawdown:.2f}, "
            f"historical cumulative loss={cumulative_loss:.2f}."
        )

        return ScenarioMatch(
            scenario_id=str(replay.get("scenario", "unknown")),
            scenario_type="historical_replay",
            similarity_score=score,
            explanation=explanation,
        )

    def score_stress_test(
        self,
        live_state: Dict[str, Any],
        scenario: Dict[str, Any],
    ) -> ScenarioMatch:
        stress_score = float(live_state.get("market_stress_score", 0.0))
        state_label = str(live_state.get("state_label", "unknown")).lower()

        impact = abs(float(scenario.get("portfolio_impact", 0.0)))

        scenario_stress = min(impact * 3.0, 1.0)

        score = 1.0 - abs(stress_score - scenario_stress)

        if state_label in {"stressed", "critical"} and impact >= 0.05:
            score += 0.10

        score = round(max(min(score, 1.0), 0.0), 4)

        explanation = (
            f"Live stress={stress_score:.2f}, "
            f"scenario impact={impact:.2f}, "
            f"severity={scenario.get('severity')}."
        )

        return ScenarioMatch(
            scenario_id=str(scenario.get("scenario_id", "unknown")),
            scenario_type="synthetic_stress_test",
            similarity_score=score,
            explanation=explanation,
        )

    def run(self) -> ScenarioMatchingResult:
        live_state = self.load_json(LIVE_STATE_PATH)
        historical_replays = self.load_json(HISTORICAL_REPLAY_PATH)
        stress_tests = self.load_json(STRESS_TEST_PATH)

        if not isinstance(live_state, dict) or not live_state:
            raise FileNotFoundError(
                f"Missing live state file: {LIVE_STATE_PATH}. "
                "Run python -m src.digital_twin.live_digital_twin_state_engine first."
            )

        matches: List[ScenarioMatch] = []

        if isinstance(historical_replays, list):
            for replay in historical_replays:
                if replay.get("observations", 0) > 0:
                    matches.append(
                        self.score_historical_replay(
                            live_state=live_state,
                            replay=replay,
                        )
                    )

        if isinstance(stress_tests, list):
            for scenario in stress_tests:
                matches.append(
                    self.score_stress_test(
                        live_state=live_state,
                        scenario=scenario,
                    )
                )

        matches = sorted(
            matches,
            key=lambda x: x.similarity_score,
            reverse=True,
        )

        if not matches:
            raise ValueError("No scenarios available for matching.")

        closest = matches[0]

        result = ScenarioMatchingResult(
            timestamp_utc=str(live_state.get("timestamp_utc")),
            live_state_label=str(live_state.get("state_label", "unknown")),
            market_stress_score=float(live_state.get("market_stress_score", 0.0)),
            closest_scenario=closest.scenario_id,
            closest_scenario_type=closest.scenario_type,
            closest_similarity_score=closest.similarity_score,
            matches=matches,
        )

        self.write_outputs(result)
        return result

    def write_outputs(self, result: ScenarioMatchingResult) -> None:
        json_path = OUTPUT_DIR / "live_scenario_match.json"
        csv_path = OUTPUT_DIR / "live_scenario_matches.csv"
        txt_path = OUTPUT_DIR / "live_scenario_match_report.txt"

        data = asdict(result)

        json_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

        import pandas as pd

        pd.DataFrame(
            [asdict(match) for match in result.matches]
        ).to_csv(
            csv_path,
            index=False,
        )

        lines = [
            "=" * 80,
            "AURUM LIVE SCENARIO MATCHING ENGINE",
            "=" * 80,
            f"Timestamp UTC: {result.timestamp_utc}",
            f"Live State Label: {result.live_state_label}",
            f"Market Stress Score: {result.market_stress_score}",
            "-" * 80,
            f"Closest Scenario: {result.closest_scenario}",
            f"Scenario Type: {result.closest_scenario_type}",
            f"Similarity Score: {result.closest_similarity_score}",
            "",
            "Top Matches:",
        ]

        for match in result.matches[:10]:
            lines.append(
                f"  {match.scenario_id:<30} "
                f"{match.scenario_type:<25} "
                f"score={match.similarity_score:.4f}"
            )

        txt_path.write_text("\n".join(lines), encoding="utf-8")

    def print_result(self, result: ScenarioMatchingResult) -> None:
        print("=" * 80)
        print("AURUM LIVE SCENARIO MATCHING ENGINE")
        print("=" * 80)
        print(f"Live State: {result.live_state_label}")
        print(f"Stress Score: {result.market_stress_score}")
        print("-" * 80)
        print(f"Closest Scenario: {result.closest_scenario}")
        print(f"Scenario Type: {result.closest_scenario_type}")
        print(f"Similarity Score: {result.closest_similarity_score}")
        print("-" * 80)
        print("Top Matches:")
        for match in result.matches[:10]:
            print(
                f"{match.scenario_id:<30} "
                f"{match.scenario_type:<25} "
                f"score={match.similarity_score:.4f}"
            )


def main() -> None:
    engine = LiveScenarioMatchingEngine()
    result = engine.run()
    engine.print_result(result)


if __name__ == "__main__":
    main()