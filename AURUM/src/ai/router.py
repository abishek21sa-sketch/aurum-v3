import json

from src.ai.orchestrator import analyze_portfolio_report
from src.ai.structured_report import generate_structured_portfolio_report
from src.ai.tools import read_text_report, format_memory_context
from src.ai.llm_client import query_llm
from src.ai.memory import update_memory
from datetime import datetime
from pathlib import Path


def save_router_output(result, output_path: str):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(result, dict):
        path.write_text(json.dumps(result, indent=4), encoding="utf-8")
    else:
        path.write_text(str(result), encoding="utf-8")


class AIRouter:

    def route(self, task: str):

        task = task.lower()

        if "executive" in task:

            return analyze_portfolio_report(
                report_path="results/reports/portfolio_optimization_report.txt",
                analysis_type="executive"
            )

        elif "technical" in task:
            portfolio_report = read_text_report(
                "results/reports/portfolio_optimization_report.txt"
            )

            memory_context = format_memory_context()

            return query_llm(
                user_query="""   
                Write a technical quantitative interpretation of this portfolio optimization report.
        
                Use the prior AI memory to connect the portfolio interpretation with the latest
                known market regime and risk signal.
                Discuss:
                - objective function
                - constraints
                - covariance structure
                - marginal risk
                - zero allocations
                - whether the allocation is consistent with the latest remembered market regime
                """,
                context=f"{portfolio_report}\n\n{memory_context}"
            )

        elif "structured" in task:

            return generate_structured_portfolio_report(
                report_path="results/reports/portfolio_optimization_report.txt",
                output_path="results/reports/router_structured_output.json"
            )

        elif "market signal" in task:

            signal_report = read_text_report(
                "results/reports/market_signal_report.txt"
            )

            result = query_llm(
                user_query="""
                Analyze the current market signal report.
                Discuss:
                - market regime
                - risk sentiment
                - possible allocation implications
                - defensive vs aggressive positioning
                """,
                context=signal_report
            )

            update_memory(
                "last_market_signal_analysis_time",
                str(datetime.now())
            )

            update_memory(
                "latest_market_analysis",
                result
            )

            return result
            

        else:
            return "No matching AI workflow found."


if __name__ == "__main__":

    router = AIRouter()

    tasks = {
        "market_signal": "Analyze market signal report",
        "executive": "Generate executive portfolio analysis",
        "technical": "Generate technical portfolio analysis",
        "structured": "Generate structured portfolio analysis"
    }

    for name, task in tasks.items():
        result = router.route(task)

        output_path = f"results/reports/router_{name}_output.txt"
        if isinstance(result, dict):
            output_path = f"results/reports/router_{name}_output.json"

        save_router_output(result, output_path)

        print(f"Saved {name} output to: {output_path}")
