import json
from pathlib import Path

from src.ai.llm_client import query_llm_structured
from src.ai.tools import read_text_report, format_portfolio_context


def generate_structured_portfolio_report(
    report_path: str,
    output_path: str
):
    report_text = read_text_report(report_path)
    context = format_portfolio_context(report_text)

    result = query_llm_structured(
        user_query="Analyze this portfolio optimization report.",
        context=context
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_file.write_text(
        json.dumps(result, indent=4),
        encoding="utf-8"
    )

    return result


if __name__ == "__main__":
    result = generate_structured_portfolio_report(
        report_path="results/reports/portfolio_optimization_report.txt",
        output_path="results/reports/ai_structured_portfolio_report.json"
    )

    print("\nSTRUCTURED PORTFOLIO REPORT")
    print("=" * 70)
    print(json.dumps(result, indent=4))
