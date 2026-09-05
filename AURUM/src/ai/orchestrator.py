from pathlib import Path

from src.ai.llm_client import query_llm
from src.ai.tools import read_text_report, format_portfolio_context


def analyze_portfolio_report(report_path: str, analysis_type: str):
    report_text = read_text_report(report_path)
    context = format_portfolio_context(report_text)

    if analysis_type == "executive":
        user_query = """
        Write an executive-level summary of this portfolio optimization report.
        Focus on business interpretation, risk posture, and allocation logic.
        Avoid equations.
        """
    elif analysis_type == "technical":
        user_query = """
        Write a technical quantitative interpretation of this portfolio optimization report.
        Discuss objective function, constraints, covariance structure, marginal risk,
        and why certain assets receive zero allocation.
        """
    else:
        raise ValueError("analysis_type must be either 'executive' or 'technical'")

    return query_llm(
        user_query=user_query,
        context=context
    )


def save_ai_report(ai_text: str, output_path: str):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ai_text, encoding="utf-8")


if __name__ == "__main__":
    report_path = "results/reports/portfolio_optimization_report.txt"

    executive_summary = analyze_portfolio_report(
        report_path=report_path,
        analysis_type="executive"
    )

    technical_summary = analyze_portfolio_report(
        report_path=report_path,
        analysis_type="technical"
    )

    save_ai_report(
        executive_summary,
        "results/reports/ai_portfolio_executive_summary.txt"
    )

    save_ai_report(
        technical_summary,
        "results/reports/ai_portfolio_technical_summary.txt"
    )

    print("\nAURUM AI EXECUTIVE SUMMARY")
    print("=" * 70)
    print(executive_summary)

    print("\nAURUM AI TECHNICAL SUMMARY")
    print("=" * 70)
    print(technical_summary)

    print("\nSaved:")
    print("- results/reports/ai_portfolio_executive_summary.txt")
    print("- results/reports/ai_portfolio_technical_summary.txt")
