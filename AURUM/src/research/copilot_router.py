from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


VALID_ACTIONS = {
    "SHOW_TOP_RISKS",
    "COMPARE_PORTFOLIOS",
    "RUN_FED_SHOCK",
    "RUN_ASSET_SHOCK",
    "GOVERNANCE_STATUS",
    "MEMORY_LOOKUP",
    "DECISION_EXPLANATION",
    "GENERAL_PORTFOLIO_ANSWER",
}


@dataclass
class CopilotRoute:
    user_query: str
    action: str
    confidence: float
    entities: Dict[str, str]
    reasoning: str


class CopilotRouter:
    """
    Routes natural-language user questions to AURUM portfolio/risk/governance actions.
    """

    def route(self, user_query: str) -> CopilotRoute:
        q = user_query.lower().strip()

        entities: Dict[str, str] = {}

        if any(x in q for x in ["top risks", "main risks", "biggest risks", "show risks"]):
            return CopilotRoute(
                user_query=user_query,
                action="SHOW_TOP_RISKS",
                confidence=0.95,
                entities=entities,
                reasoning="Query asks for current portfolio risk summary.",
            )

        if "compare" in q and "defensive" in q:
            return CopilotRoute(
                user_query=user_query,
                action="COMPARE_PORTFOLIOS",
                confidence=0.94,
                entities={"comparison_target": "defensive_portfolio"},
                reasoning="Query asks to compare current portfolio to defensive portfolio.",
            )

        if "fed" in q and any(x in q for x in ["shock", "hike", "rate", "rates"]):
            return CopilotRoute(
                user_query=user_query,
                action="RUN_FED_SHOCK",
                confidence=0.93,
                entities={"shock_type": "fed_rate_shock"},
                reasoning="Query asks for Fed/rate shock scenario.",
            )

        if "falls" in q or "drops" in q or "down" in q:
            asset = self._extract_asset(q)
            if asset:
                entities["asset"] = asset
                entities["shock"] = self._extract_percent(q) or "-20%"
                return CopilotRoute(
                    user_query=user_query,
                    action="RUN_ASSET_SHOCK",
                    confidence=0.90,
                    entities=entities,
                    reasoning="Query asks for single-asset downside shock.",
                )

        if any(x in q for x in ["governance", "compliance", "approval", "blocked", "risk officer"]):
            return CopilotRoute(
                user_query=user_query,
                action="GOVERNANCE_STATUS",
                confidence=0.92,
                entities=entities,
                reasoning="Query asks for governance/risk officer status.",
            )

        if any(x in q for x in ["seen this before", "memory", "historical", "similar"]):
            return CopilotRoute(
                user_query=user_query,
                action="MEMORY_LOOKUP",
                confidence=0.91,
                entities=entities,
                reasoning="Query asks for institutional memory lookup.",
            )

        if any(x in q for x in ["why", "explain", "reason", "decision"]):
            return CopilotRoute(
                user_query=user_query,
                action="DECISION_EXPLANATION",
                confidence=0.90,
                entities=entities,
                reasoning="Query asks for decision explanation.",
            )

        return CopilotRoute(
            user_query=user_query,
            action="GENERAL_PORTFOLIO_ANSWER",
            confidence=0.65,
            entities=entities,
            reasoning="Query routed to general portfolio copilot response.",
        )

    @staticmethod
    def _extract_asset(q: str) -> str | None:
        known_assets = [
            "SPY", "QQQ", "DIA", "TLT", "GLD", "BTC", "BTC-USD",
            "ETH", "ETH-USD", "VIX", "NVDA", "AAPL", "MSFT", "TSLA",
        ]

        q_upper = q.upper()

        for asset in known_assets:
            if asset in q_upper:
                return asset

        return None

    @staticmethod
    def _extract_percent(q: str) -> str | None:
        tokens = q.replace("%", " %").split()

        for i, token in enumerate(tokens):
            if token == "%" and i > 0:
                try:
                    value = float(tokens[i - 1])
                    return f"-{abs(value)}%"
                except Exception:
                    continue

            if token.endswith("%"):
                try:
                    value = float(token.replace("%", ""))
                    return f"-{abs(value)}%"
                except Exception:
                    continue

        return None


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5E COPILOT ROUTER")
    print("=" * 80)

    router = CopilotRouter()

    examples: List[str] = [
        "Show top risks.",
        "Compare current portfolio to defensive portfolio.",
        "Run a Fed shock.",
        "What happens if NVDA falls 20%?",
        "Why are we defensive?",
        "Have we seen this before?",
        "What is governance status?",
    ]

    for q in examples:
        route = router.route(q)
        print("-" * 80)
        print(f"Query:      {q}")
        print(f"Action:     {route.action}")
        print(f"Confidence: {route.confidence}")
        print(f"Entities:   {route.entities}")

    print("=" * 80)


if __name__ == "__main__":
    main()