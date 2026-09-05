from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.research.ai_runtime_config import load_ai_settings, LLMCallBudget
from src.research.committee_context_builder import CommitteeContextBuilder


RESULTS_DIR = Path("results/research")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_text(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write(text)


def extract_json(raw: str) -> Dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    start = raw.find("{")
    end = raw.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model response: {raw[:500]}")

    return json.loads(raw[start : end + 1])


class TrueLLMClient:
    def __init__(self, model: Optional[str] = None):
        settings = load_ai_settings()

        self.settings = settings
        self.model = model or os.getenv(
            "AURUM_LLM_MODEL",
            settings.get("default_model", "gpt-4o-mini"),
        )
        self.budget = LLMCallBudget(int(settings.get("max_llm_calls_per_run", 20)))
        self.backend = None
        self.client = None

        if not settings.get("ai_enabled", True):
            raise RuntimeError("AI is disabled in config/ai_settings.json")

        try:
            from src.research.llm_client import LLMClient  # type: ignore

            self.client = LLMClient()
            self.backend = "aurum_llm_client"
            return
        except Exception:
            pass

        try:
            from openai import OpenAI  # type: ignore

            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError("OPENAI_API_KEY not found")

            self.client = OpenAI()
            self.backend = "openai"
            return

        except Exception as exc:
            raise RuntimeError(
                "No real LLM backend available. Set OPENAI_API_KEY or fix src.research.llm_client."
            ) from exc

    def complete_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        self.budget.consume()

        if self.backend == "aurum_llm_client":
            if hasattr(self.client, "complete_json"):
                return self.client.complete_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            if hasattr(self.client, "chat_json"):
                return self.client.chat_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            if hasattr(self.client, "chat"):
                raw = self.client.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                return extract_json(raw)

            raise RuntimeError(
                "src.research.llm_client exists but has no supported JSON chat method."
            )

        if self.backend == "openai":
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
            except Exception as exc:
                if "temperature" not in str(exc):
                    raise

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )

            content = response.choices[0].message.content or "{}"
            return json.loads(content)

        raise RuntimeError("Unsupported LLM backend")

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        self.budget.consume()

        if self.backend == "aurum_llm_client":
            if hasattr(self.client, "complete"):
                return self.client.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            if hasattr(self.client, "chat"):
                return self.client.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )

            raise RuntimeError(
                "src.research.llm_client exists but has no supported text chat method."
            )

        if self.backend == "openai":
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=0.25,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
            except Exception as exc:
                if "temperature" not in str(exc):
                    raise

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )

            return response.choices[0].message.content or ""

        raise RuntimeError("Unsupported LLM backend")


@dataclass
class CommitteeAgent:
    name: str
    role: str
    mandate: str
    voting_bias: str


AGENTS: List[CommitteeAgent] = [
    CommitteeAgent(
        name="Macro Agent",
        role="Macroeconomic strategist",
        mandate="Evaluate inflation, rates, growth, liquidity, and cross-asset macro pressure.",
        voting_bias="Protect portfolio from macro regime deterioration.",
    ),
    CommitteeAgent(
        name="Risk Agent",
        role="Chief risk officer",
        mandate="Evaluate VaR, CVaR, drawdown, stress tests, tail risk, and governance blocks.",
        voting_bias="Prefer capital preservation when downside risk is elevated.",
    ),
    CommitteeAgent(
        name="Portfolio Agent",
        role="Portfolio construction specialist",
        mandate="Evaluate weights, concentration, diversification, turnover, and allocation quality.",
        voting_bias="Prefer efficient allocation with controlled concentration and turnover.",
    ),
    CommitteeAgent(
        name="Digital Twin Agent",
        role="Simulation and stress-testing specialist",
        mandate="Evaluate Monte Carlo survival, stress scenarios, contagion, and live twin state.",
        voting_bias="Prefer de-risking when simulations show fragility.",
    ),
    CommitteeAgent(
        name="Market Structure Agent",
        role="Market microstructure and technical conditions specialist",
        mandate="Evaluate breadth, momentum, volatility, liquidity, trend health, and execution conditions.",
        voting_bias="Prefer exposure only when structure confirms regime quality.",
    ),
]


class AIInvestmentCommittee:
    def __init__(self, llm: Optional[TrueLLMClient] = None):
        self.llm = llm or TrueLLMClient()

    def run(self) -> Dict[str, Any]:
        packet = self._load_research_packet()
        settings = load_ai_settings()
        phase5b_settings = settings.get("phase5b", {})
        committee_mode = phase5b_settings.get("committee_mode", "single_call")

        if committee_mode == "single_call":
            return self._run_single_call_committee(packet)

        opinions = [self._agent_opinion(agent, packet) for agent in AGENTS]
        debates = [self._agent_rebuttal(agent, packet, opinions) for agent in AGENTS]
        votes = [self._agent_vote(agent, packet, opinions, debates) for agent in AGENTS]

        portfolio_manager_recommendation = self._portfolio_manager_recommendation(
            packet,
            opinions,
            debates,
            votes,
        )

        final_decision = self._chair_decision(
            packet,
            opinions,
            debates,
            votes,
            portfolio_manager_recommendation,
        )

        minutes = {
            "generated_at": utc_now(),
            "committee_type": "true_llm_multi_agent_investment_committee",
            "committee_mode": "full_multi_agent",
            "llm_backend": self.llm.backend,
            "model": self.llm.model,
            "research_packet_used": True,
            "llm_calls_used": self.llm.budget.calls_used,
            "llm_call_budget": self.llm.budget.max_calls,
            "agents": [asdict(a) for a in AGENTS],
            "agent_opinions": opinions,
            "agent_rebuttals": debates,
            "votes": votes,
            "portfolio_manager_recommendation": portfolio_manager_recommendation,
            "final_decision": final_decision,
        }

        self._save_outputs(minutes)
        return minutes

    def _load_research_packet(self) -> Dict[str, Any]:
        candidates = [
            RESULTS_DIR / "ai_daily_research_packet.json",
            RESULTS_DIR / "ai_research_committee.json",
            RESULTS_DIR / "ai_research_desk_orchestrator.json",
        ]

        packet: Dict[str, Any] = {}
        for path in candidates:
            if path.exists():
                packet[path.name] = load_json(path)

        if not packet:
            raise FileNotFoundError("No AI research packet found. Run Phase 5A first.")

        return packet

    def _run_single_call_committee(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        system = """
You are the AURUM AI Investment Committee.

Simulate a full institutional investment committee in ONE response.

Committee members:
1. Macro Agent
2. Risk Agent
3. Portfolio Agent
4. Digital Twin Agent
5. Market Structure Agent
6. AI Portfolio Manager
7. Committee Chair

You must produce:
- agent_opinions
- agent_rebuttals
- votes
- portfolio_manager_recommendation
- final_decision

Use only the provided compressed committee context.
Do not invent market data.
Return strict JSON only.
"""

        context = CommitteeContextBuilder().build()

        user = f"""
Compressed committee context:
{json.dumps(context, indent=2)[:9000]}

Return JSON with this exact top-level schema:
{{
  "agent_opinions": [],
  "agent_rebuttals": [],
  "votes": [],
  "portfolio_manager_recommendation": {{}},
  "final_decision": {{}}
}}

Rules:
- agent_opinions must contain exactly 5 entries.
- agent_rebuttals must contain exactly 5 entries.
- votes must contain exactly 5 entries.
- If execution_permission is blocked, votes should usually be block_execution.
- Still provide investment_view separately from execution_permission.
- Target allocation may be prepared_only, but do not claim execution.
"""

        result = self.llm.complete_json(system, user)
        result = self._repair_single_call_committee_result(result)

        agent_opinions = result["agent_opinions"]
        agent_rebuttals = result["agent_rebuttals"]
        votes = result["votes"]
        pm = result["portfolio_manager_recommendation"]
        final_decision = result["final_decision"]

        minutes = {
            "generated_at": utc_now(),
            "committee_type": "true_llm_single_call_investment_committee",
            "committee_mode": "single_call",
            "llm_backend": self.llm.backend,
            "model": self.llm.model,
            "research_packet_used": True,
            "llm_calls_used": self.llm.budget.calls_used,
            "llm_call_budget": self.llm.budget.max_calls,
            "agents": [asdict(a) for a in AGENTS],
            "agent_opinions": agent_opinions,
            "agent_rebuttals": agent_rebuttals,
            "votes": votes,
            "portfolio_manager_recommendation": pm,
            "final_decision": final_decision,
        }

        self._save_outputs(minutes)
        return minutes

    def _repair_single_call_committee_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(result, dict):
            result = {}

        final_decision = result.get("final_decision")
        if not isinstance(final_decision, dict):
            final_decision = {}

        pm = result.get("portfolio_manager_recommendation")
        if not isinstance(pm, dict):
            pm = {}

        investment_view = (
            final_decision.get("investment_view")
            or pm.get("portfolio_manager_view")
            or "defensive"
        )
        if investment_view not in ["risk_on", "neutral", "defensive", "risk_off"]:
            investment_view = "defensive"

        execution_permission = (
            final_decision.get("execution_permission")
            or pm.get("execution_permission")
            or "blocked"
        )
        if execution_permission not in ["allowed", "review_required", "blocked"]:
            execution_permission = "blocked"

        approval_status = final_decision.get("approval_status") or (
            "blocked" if execution_permission == "blocked" else "review_required"
        )

        opinions = result.get("agent_opinions")
        if not isinstance(opinions, list) or len(opinions) < 5:
            opinions = self._default_agent_opinions(investment_view, execution_permission)
        else:
            opinions = opinions[:5]

        rebuttals = result.get("agent_rebuttals")
        if not isinstance(rebuttals, list) or len(rebuttals) < 5:
            rebuttals = self._default_agent_rebuttals(opinions, investment_view)
        else:
            rebuttals = rebuttals[:5]

        votes = result.get("votes")
        if not isinstance(votes, list) or len(votes) < 5:
            votes = self._default_agent_votes(opinions, investment_view, execution_permission)
        else:
            votes = votes[:5]

        pm = self._repair_portfolio_manager(pm, investment_view, execution_permission)
        final_decision = self._repair_final_decision(
            final_decision,
            pm,
            votes,
            investment_view,
            execution_permission,
            approval_status,
        )

        return {
            "agent_opinions": opinions,
            "agent_rebuttals": rebuttals,
            "votes": votes,
            "portfolio_manager_recommendation": pm,
            "final_decision": final_decision,
        }

    def _default_agent_opinions(
        self,
        investment_view: str,
        execution_permission: str,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "agent": "Macro Agent",
                "stance": "neutral",
                "confidence": 0.75,
                "key_observations": [
                    "Compressed context does not indicate a standalone macro crisis.",
                    "Governance and execution permission dominate the final action."
                ],
                "main_concern": "Macro signals cannot override governance controls.",
                "recommended_actions": [
                    {
                        "asset": "PORTFOLIO",
                        "action": "review",
                        "change_pct": 0.0,
                        "rationale": "Review macro posture after governance and risk reconciliation."
                    }
                ],
                "risk_flags": ["execution_permission_blocked"],
                "what_would_change_my_view": "Governance clearance and updated macro data."
            },
            {
                "agent": "Risk Agent",
                "stance": "defensive",
                "confidence": 0.86,
                "key_observations": [
                    "Execution permission is blocked.",
                    "Risk methodology and portfolio-state reconciliation are required."
                ],
                "main_concern": "Risk controls are binding.",
                "recommended_actions": [
                    {
                        "asset": "PORTFOLIO",
                        "action": "review",
                        "change_pct": 0.0,
                        "rationale": "Validate VaR, CVaR, drawdown, risk budget, and exposure state."
                    }
                ],
                "risk_flags": ["governance_block", "risk_reconciliation_required"],
                "what_would_change_my_view": "Compliance remediated and risk metrics validated."
            },
            {
                "agent": "Portfolio Agent",
                "stance": investment_view,
                "confidence": 0.82,
                "key_observations": [
                    "Portfolio recommendations are not executable while blocked.",
                    "Prepared-only guidance may be reviewed after clearance."
                ],
                "main_concern": "Allocation cannot become executable until governance clears.",
                "recommended_actions": [
                    {
                        "asset": "PORTFOLIO",
                        "action": "hold",
                        "change_pct": 0.0,
                        "rationale": "Maintain passive hold while blocked."
                    }
                ],
                "risk_flags": ["non_executable_allocation"],
                "what_would_change_my_view": "Formal execution permission restored."
            },
            {
                "agent": "Digital Twin Agent",
                "stance": "defensive",
                "confidence": 0.80,
                "key_observations": [
                    "Stress and drawdown methodology require validation.",
                    "Execution remains blocked pending reconciliation."
                ],
                "main_concern": "Stress-test uncertainty.",
                "recommended_actions": [
                    {
                        "asset": "SPY/QQQ/DIA",
                        "action": "hedge",
                        "change_pct": 0.0,
                        "rationale": "Prepare hedge plan but do not execute."
                    }
                ],
                "risk_flags": ["stress_validation_required"],
                "what_would_change_my_view": "Digital twin validates acceptable downside."
            },
            {
                "agent": "Market Structure Agent",
                "stance": "neutral",
                "confidence": 0.74,
                "key_observations": [
                    "Market structure is secondary to governance.",
                    "Volatility and liquidity should continue to be monitored."
                ],
                "main_concern": "No market-structure signal can authorize execution while blocked.",
                "recommended_actions": [
                    {
                        "asset": "VIX",
                        "action": "review",
                        "change_pct": 0.0,
                        "rationale": "Monitor volatility and market stress."
                    }
                ],
                "risk_flags": ["execution_blocked"],
                "what_would_change_my_view": "Execution restored and market structure confirms posture."
            },
        ]

    def _default_agent_rebuttals(
        self,
        opinions: List[Dict[str, Any]],
        investment_view: str,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "agent": opinion.get("agent", "Unknown Agent"),
                "agreements": [
                    "Execution permission is the binding constraint."
                ],
                "disagreements": [
                    "Underlying market posture may differ, but implementation remains blocked."
                ],
                "strongest_counterargument": (
                    "Constructive market signals do not override governance and compliance controls."
                ),
                "revised_stance": opinion.get("stance", investment_view),
                "revised_recommendation": (
                    "Maintain passive hold and prepare only non-executable guidance."
                ),
            }
            for opinion in opinions
        ]

    def _default_agent_votes(
        self,
        opinions: List[Dict[str, Any]],
        investment_view: str,
        execution_permission: str,
    ) -> List[Dict[str, Any]]:
        vote = "block_execution" if execution_permission == "blocked" else f"approve_{investment_view}"

        return [
            {
                "agent": opinion.get("agent", "Unknown Agent"),
                "vote": vote,
                "confidence": opinion.get("confidence", 0.8),
                "final_actions": [
                    {
                        "asset": "PORTFOLIO",
                        "action": "hold" if execution_permission == "blocked" else "review",
                        "change_pct": 0.0,
                        "rationale": (
                            "Execution is blocked; maintain passive hold."
                            if execution_permission == "blocked"
                            else "Execution may proceed only after final review."
                        ),
                    }
                ],
                "one_sentence_reason": (
                    "Execution permission is blocked, so no trade is authorized."
                    if execution_permission == "blocked"
                    else f"Committee approves {investment_view} posture subject to controls."
                ),
            }
            for opinion in opinions
        ]

    def _repair_portfolio_manager(
        self,
        pm: Dict[str, Any],
        investment_view: str,
        execution_permission: str,
    ) -> Dict[str, Any]:
        target = pm.get("target_allocation")
        if not isinstance(target, dict) or not target:
            target = self._default_target_allocation(investment_view)

        status = "prepared_only" if execution_permission == "blocked" else "executable"

        allocation_changes = pm.get("allocation_changes")
        if not isinstance(allocation_changes, list) or len(allocation_changes) < 5:
            allocation_changes = []
            for asset, weight in target.items():
                allocation_changes.append(
                    {
                        "asset": asset,
                        "action": self._default_action_for_asset(asset, investment_view),
                        "target_weight": weight,
                        "change_pct": 0.0,
                        "execution_status": status,
                        "rationale": (
                            f"Prepared target from compressed committee view. "
                            f"Investment view={investment_view}; execution_permission={execution_permission}."
                        ),
                    }
                )

        return {
            "portfolio_manager_type": pm.get(
                "portfolio_manager_type",
                "single_call_ai_committee_allocator",
            ),
            "portfolio_manager_view": pm.get("portfolio_manager_view", investment_view),
            "execution_permission": pm.get("execution_permission", execution_permission),
            "recommendation_status": pm.get("recommendation_status", status),
            "manager_confidence": pm.get("manager_confidence", 0.85),
            "target_allocation": target,
            "allocation_changes": allocation_changes,
            "portfolio_rationale": pm.get(
                "portfolio_rationale",
                "Prepared-only allocation guidance generated from compressed committee context.",
            ),
            "main_tradeoff": pm.get(
                "main_tradeoff",
                "Balance risk reduction with governance constraints and liquidity preservation.",
            ),
            "risk_budget_view": pm.get(
                "risk_budget_view",
                "Risk budget must be validated before execution.",
            ),
            "what_to_do_if_governance_clears": pm.get(
                "what_to_do_if_governance_clears",
                [
                    "Reconcile latest portfolio state.",
                    "Prioritize risk-reducing trades first.",
                    "Validate post-trade risk.",
                ],
            ),
            "what_to_do_if_governance_stays_blocked": pm.get(
                "what_to_do_if_governance_stays_blocked",
                [
                    "Do not execute trades.",
                    "Maintain passive hold.",
                    "Keep guidance prepared-only.",
                ],
            ),
        }

    def _default_target_allocation(self, view: str) -> Dict[str, float]:
        if view == "risk_off":
            return {
                "SPY": 0.12,
                "QQQ": 0.08,
                "DIA": 0.08,
                "TLT": 0.24,
                "GLD": 0.16,
                "BTC": 0.03,
                "ETH": 0.02,
                "VIX": 0.05,
                "CASH": 0.22,
            }

        if view == "defensive":
            return {
                "SPY": 0.16,
                "QQQ": 0.12,
                "DIA": 0.10,
                "TLT": 0.22,
                "GLD": 0.15,
                "BTC": 0.04,
                "ETH": 0.02,
                "VIX": 0.04,
                "CASH": 0.15,
            }

        if view == "risk_on":
            return {
                "SPY": 0.24,
                "QQQ": 0.24,
                "DIA": 0.12,
                "TLT": 0.12,
                "GLD": 0.08,
                "BTC": 0.08,
                "ETH": 0.05,
                "VIX": 0.01,
                "CASH": 0.06,
            }

        return {
            "SPY": 0.20,
            "QQQ": 0.18,
            "DIA": 0.12,
            "TLT": 0.18,
            "GLD": 0.12,
            "BTC": 0.06,
            "ETH": 0.04,
            "VIX": 0.02,
            "CASH": 0.08,
        }

    def _default_action_for_asset(self, asset: str, view: str) -> str:
        if view in ["defensive", "risk_off"]:
            if asset in ["SPY", "QQQ", "DIA", "BTC", "ETH"]:
                return "decrease"
            if asset in ["TLT", "GLD", "VIX", "CASH"]:
                return "increase"
        if view == "risk_on":
            if asset in ["SPY", "QQQ", "BTC", "ETH"]:
                return "increase"
            if asset in ["CASH", "VIX"]:
                return "decrease"
        return "hold"

    def _repair_final_decision(
        self,
        final_decision: Dict[str, Any],
        pm: Dict[str, Any],
        votes: List[Dict[str, Any]],
        investment_view: str,
        execution_permission: str,
        approval_status: str,
    ) -> Dict[str, Any]:
        vote_summary = {
            "approve_risk_on": sum(1 for v in votes if v.get("vote") == "approve_risk_on"),
            "approve_neutral": sum(1 for v in votes if v.get("vote") == "approve_neutral"),
            "approve_defensive": sum(1 for v in votes if v.get("vote") == "approve_defensive"),
            "approve_risk_off": sum(1 for v in votes if v.get("vote") == "approve_risk_off"),
            "block_execution": sum(1 for v in votes if v.get("vote") == "block_execution"),
        }

        target = final_decision.get("target_allocation")
        if not isinstance(target, dict) or not target:
            target = pm.get("target_allocation", self._default_target_allocation(investment_view))

        actions = final_decision.get("portfolio_actions")
        if not isinstance(actions, list) or not actions:
            actions = [
                {
                    "asset": "PORTFOLIO",
                    "action": "hold" if execution_permission == "blocked" else "review",
                    "change_pct": 0.0,
                    "priority": "high",
                    "execution_status": "prepared_only" if execution_permission == "blocked" else "executable",
                    "rationale": (
                        "Maintain passive hold while execution is blocked."
                        if execution_permission == "blocked"
                        else "Review target allocation before execution."
                    ),
                }
            ]

        return {
            "generated_at": final_decision.get("generated_at", utc_now()),
            "investment_view": investment_view,
            "execution_permission": execution_permission,
            "approval_status": approval_status,
            "committee_confidence": final_decision.get("committee_confidence", 0.85),
            "vote_summary": vote_summary,
            "portfolio_manager_summary": final_decision.get(
                "portfolio_manager_summary",
                pm.get("portfolio_rationale", ""),
            ),
            "final_recommendation": final_decision.get(
                "final_recommendation",
                "Do not execute trades while governance remains blocked."
                if execution_permission == "blocked"
                else "Proceed only after final governance and risk review.",
            ),
            "target_allocation": target,
            "portfolio_actions": actions,
            "execution_blockers": final_decision.get(
                "execution_blockers",
                ["execution_permission_blocked"] if execution_permission == "blocked" else [],
            ),
            "risk_controls": final_decision.get(
                "risk_controls",
                [
                    "No execution until governance clears.",
                    "Validate risk metrics before approving trades.",
                    "Maintain audit trail for committee decision.",
                ],
            ),
            "conditions_for_execution": final_decision.get(
                "conditions_for_execution",
                [
                    "Governance block cleared.",
                    "Compliance status remediated.",
                    "Risk budget validated.",
                    "Portfolio state reconciled.",
                ],
            ),
            "minority_opinions": final_decision.get("minority_opinions", []),
            "executive_summary": final_decision.get(
                "executive_summary",
                f"Investment view is {investment_view}; execution permission is {execution_permission}.",
            ),
        }

    def _agent_opinion(self, agent: CommitteeAgent, packet: Dict[str, Any]) -> Dict[str, Any]:
        system = f"""
You are {agent.name}, serving as {agent.role} for AURUM.
Mandate: {agent.mandate}
Voting bias: {agent.voting_bias}
Return strict JSON only.
"""
        user = f"""
Research packet:
{json.dumps(packet, indent=2)[:30000]}

Return JSON:
{{
  "agent": "{agent.name}",
  "stance": "risk_on | neutral | defensive | risk_off",
  "confidence": 0.0,
  "key_observations": ["..."],
  "main_concern": "...",
  "recommended_actions": [],
  "risk_flags": ["..."],
  "what_would_change_my_view": "..."
}}
"""
        return self.llm.complete_json(system, user)

    def _agent_rebuttal(
        self,
        agent: CommitteeAgent,
        packet: Dict[str, Any],
        opinions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        system = f"""
You are {agent.name}. Review the other committee agents' opinions.
Return strict JSON only.
"""
        user = f"""
Research packet:
{json.dumps(packet, indent=2)[:18000]}

Committee opinions:
{json.dumps(opinions, indent=2)[:18000]}

Return JSON:
{{
  "agent": "{agent.name}",
  "agreements": ["..."],
  "disagreements": ["..."],
  "strongest_counterargument": "...",
  "revised_stance": "risk_on | neutral | defensive | risk_off",
  "revised_recommendation": "..."
}}
"""
        return self.llm.complete_json(system, user)

    def _agent_vote(
        self,
        agent: CommitteeAgent,
        packet: Dict[str, Any],
        opinions: List[Dict[str, Any]],
        debates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        system = f"""
You are {agent.name}. Cast your final committee vote.
Return strict JSON only.
"""
        user = f"""
Research packet:
{json.dumps(packet, indent=2)[:12000]}

Opinions:
{json.dumps(opinions, indent=2)[:12000]}

Debate:
{json.dumps(debates, indent=2)[:12000]}

Return JSON:
{{
  "agent": "{agent.name}",
  "vote": "approve_risk_on | approve_neutral | approve_defensive | approve_risk_off | block_execution",
  "confidence": 0.0,
  "final_actions": [],
  "one_sentence_reason": "..."
}}
"""
        return self.llm.complete_json(system, user)

    def _portfolio_manager_recommendation(
        self,
        packet: Dict[str, Any],
        opinions: List[Dict[str, Any]],
        debates: List[Dict[str, Any]],
        votes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        defensive_votes = sum(1 for v in votes if v.get("vote") == "approve_defensive")
        risk_off_votes = sum(1 for v in votes if v.get("vote") == "approve_risk_off")
        block_votes = sum(1 for v in votes if v.get("vote") == "block_execution")

        execution_permission = "blocked" if block_votes > 0 else "allowed"

        if block_votes >= 3 or defensive_votes > 0:
            manager_view = "defensive"
        elif risk_off_votes > 0:
            manager_view = "risk_off"
        else:
            manager_view = "neutral"

        target_allocation = self._default_target_allocation(manager_view)
        status = "prepared_only" if execution_permission == "blocked" else "executable"

        allocation_changes = [
            {
                "asset": asset,
                "action": self._default_action_for_asset(asset, manager_view),
                "target_weight": weight,
                "change_pct": 0.0,
                "execution_status": status,
                "rationale": (
                    f"Deterministic allocation from committee votes. "
                    f"Manager view={manager_view}; execution_permission={execution_permission}."
                ),
            }
            for asset, weight in target_allocation.items()
        ]

        return {
            "portfolio_manager_type": "deterministic_committee_allocator",
            "portfolio_manager_view": manager_view,
            "execution_permission": execution_permission,
            "recommendation_status": status,
            "manager_confidence": 0.85,
            "target_allocation": target_allocation,
            "allocation_changes": allocation_changes,
            "portfolio_rationale": "Prepared allocation derived from committee votes.",
            "main_tradeoff": "Reduce risk while preserving liquidity.",
            "risk_budget_view": "Validate risk budget before execution.",
            "what_to_do_if_governance_clears": [
                "Review target allocation against latest portfolio state.",
                "Prioritize risk-reducing trades.",
                "Validate post-trade risk.",
            ],
            "what_to_do_if_governance_stays_blocked": [
                "Do not execute trades.",
                "Maintain passive hold.",
                "Keep recommendation prepared-only.",
            ],
        }

    def _chair_decision(
        self,
        packet: Dict[str, Any],
        opinions: List[Dict[str, Any]],
        debates: List[Dict[str, Any]],
        votes: List[Dict[str, Any]],
        portfolio_manager_recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        system = """
You are the Chair of the AURUM AI Investment Committee.
Synthesize opinions, rebuttals, votes, and portfolio-manager recommendation.
Return strict JSON only.
"""
        user = f"""
Research packet:
{json.dumps(packet, indent=2)[:14000]}

Agent opinions:
{json.dumps(opinions, indent=2)[:12000]}

Debate:
{json.dumps(debates, indent=2)[:10000]}

Votes:
{json.dumps(votes, indent=2)[:10000]}

AI Portfolio Manager recommendation:
{json.dumps(portfolio_manager_recommendation, indent=2)[:12000]}

Return JSON with final_decision fields directly:
{{
  "investment_view": "risk_on | neutral | defensive | risk_off",
  "execution_permission": "allowed | review_required | blocked",
  "approval_status": "approved | review_required | blocked",
  "committee_confidence": 0.0,
  "vote_summary": {{}},
  "portfolio_manager_summary": "...",
  "final_recommendation": "...",
  "target_allocation": {{}},
  "portfolio_actions": [],
  "execution_blockers": [],
  "risk_controls": [],
  "conditions_for_execution": [],
  "minority_opinions": [],
  "executive_summary": "..."
}}
"""
        return self.llm.complete_json(system, user)

    def _save_outputs(self, minutes: Dict[str, Any]) -> None:
        save_json(RESULTS_DIR / "investment_committee_minutes.json", minutes)
        save_json(RESULTS_DIR / "committee_decision.json", minutes["final_decision"])
        save_text(
            RESULTS_DIR / "committee_explanation.txt",
            self._format_explanation(minutes),
        )

    def _format_explanation(self, minutes: Dict[str, Any]) -> str:
        decision = minutes["final_decision"]
        pm = minutes.get("portfolio_manager_recommendation", {})

        lines = []
        lines.append("=" * 80)
        lines.append("AURUM AI INVESTMENT COMMITTEE EXPLANATION")
        lines.append("=" * 80)
        lines.append(f"Generated At: {minutes['generated_at']}")
        lines.append(f"LLM Backend: {minutes['llm_backend']}")
        lines.append(f"Model: {minutes['model']}")
        lines.append(f"LLM Calls Used: {minutes.get('llm_calls_used')}/{minutes.get('llm_call_budget')}")
        lines.append("")
        lines.append("FINAL DECISION")
        lines.append("-" * 80)
        lines.append(f"Investment View: {decision.get('investment_view')}")
        lines.append(f"Execution Permission: {decision.get('execution_permission')}")
        lines.append(f"Approval Status: {decision.get('approval_status')}")
        lines.append(f"Committee Confidence: {decision.get('committee_confidence')}")
        lines.append("")
        lines.append("Executive Summary:")
        lines.append(decision.get("executive_summary", ""))
        lines.append("")
        lines.append("Final Recommendation:")
        lines.append(decision.get("final_recommendation", ""))
        lines.append("")
        lines.append("Target Allocation:")
        for asset, weight in decision.get("target_allocation", {}).items():
            lines.append(f"- {asset}: {weight}")
        lines.append("")
        lines.append("Portfolio Actions:")
        for action in decision.get("portfolio_actions", []):
            lines.append(
                f"- {action.get('asset')}: {action.get('action')} "
                f"{action.get('change_pct')} | priority={action.get('priority')} | "
                f"status={action.get('execution_status')} | {action.get('rationale')}"
            )
        lines.append("")
        lines.append("Vote Summary:")
        lines.append(json.dumps(decision.get("vote_summary", {}), indent=2))
        lines.append("")
        lines.append("Risk Controls:")
        for item in decision.get("risk_controls", []):
            lines.append(f"- {item}")
        lines.append("")
        lines.append("Conditions For Execution:")
        for item in decision.get("conditions_for_execution", []):
            lines.append(f"- {item}")

        if pm:
            lines.append("")
            lines.append("AI PORTFOLIO MANAGER RECOMMENDATION")
            lines.append("-" * 80)
            lines.append(f"Portfolio Manager Type: {pm.get('portfolio_manager_type')}")
            lines.append(f"Portfolio Manager View: {pm.get('portfolio_manager_view')}")
            lines.append(f"Recommendation Status: {pm.get('recommendation_status')}")
            lines.append(f"Manager Confidence: {pm.get('manager_confidence')}")
            lines.append("")
            lines.append("Prepared Target Allocation:")
            for asset, weight in pm.get("target_allocation", {}).items():
                lines.append(f"- {asset}: {weight}")
            lines.append("")
            lines.append("Allocation Changes:")
            for rec in pm.get("allocation_changes", []):
                lines.append(
                    f"- {rec.get('asset')}: {rec.get('action')} | "
                    f"target={rec.get('target_weight')} | "
                    f"status={rec.get('execution_status')} | {rec.get('rationale')}"
                )
            lines.append("")
            lines.append("Portfolio Rationale:")
            lines.append(pm.get("portfolio_rationale", ""))

        return "\n".join(lines)


def main() -> None:
    print("=" * 80)
    print("AURUM PHASE 5B AI INVESTMENT COMMITTEE")
    print("=" * 80)

    committee = AIInvestmentCommittee()
    minutes = committee.run()
    decision = minutes["final_decision"]

    print(f"Backend: {minutes['llm_backend']}")
    print(f"Model:   {minutes['model']}")
    print(f"LLM Calls Used: {minutes.get('llm_calls_used')}/{minutes.get('llm_call_budget')}")
    print("-" * 80)
    print(f"Investment View:      {decision.get('investment_view')}")
    print(f"Execution Permission: {decision.get('execution_permission')}")
    print(f"Approval Status:      {decision.get('approval_status')}")
    print(f"Confidence:           {decision.get('committee_confidence')}")
    print("-" * 80)
    print(decision.get("final_recommendation"))
    print("-" * 80)
    print("Saved:")
    print("results/research/investment_committee_minutes.json")
    print("results/research/committee_decision.json")
    print("results/research/committee_explanation.txt")


if __name__ == "__main__":
    main()