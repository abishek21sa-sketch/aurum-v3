from pathlib import Path
import re


SCENARIO_REPORT_PATH = Path("results/risk/live_scenario_shock_report.txt")


def load_scenario_report(path: Path = SCENARIO_REPORT_PATH) -> str:
    if not path.exists():
        raise FileNotFoundError(
            "Live scenario shock report not found. Run: python -m src.risk.live_scenario_shock_engine"
        )

    return path.read_text(encoding="utf-8")


def parse_percent(value: str):
    return float(value.replace("%", "").replace("+", "").strip())


def parse_scenario_results(report_text: str):
    pattern = re.compile(
        r"(?P<scenario>[a-zA-Z0-9_]+)\s+\|\s+"
        r"Base Impact:\s+(?P<base>[+-]?\d+\.\d+)%\s+\|\s+"
        r"Live Impact:\s+(?P<live>[+-]?\d+\.\d+)%\s+\|\s+"
        r"Overlay Delta:\s+(?P<delta>[+-]?\d+\.\d+)%\s+\|\s+"
        r"Worst Sleeve:\s+(?P<worst_sleeve>[a-zA-Z0-9_]+)"
    )

    scenarios = []

    for match in pattern.finditer(report_text):
        scenarios.append(
            {
                "scenario": match.group("scenario"),
                "base_impact_pct": parse_percent(match.group("base")),
                "live_impact_pct": parse_percent(match.group("live")),
                "overlay_delta_pct": parse_percent(match.group("delta")),
                "worst_sleeve": match.group("worst_sleeve"),
            }
        )

    return scenarios


def rank_scenarios_by_downside(scenarios):
    return sorted(scenarios, key=lambda x: x["live_impact_pct"])


def find_worst_scenario(scenarios):
    if not scenarios:
        return None
    return rank_scenarios_by_downside(scenarios)[0]


def find_best_scenario(scenarios):
    if not scenarios:
        return None
    return sorted(scenarios, key=lambda x: x["live_impact_pct"], reverse=True)[0]


def format_scenario_table(scenarios):
    lines = []
    lines.append("PARSED LIVE SCENARIO RESULTS")
    lines.append("=" * 70)
    lines.append(
        f"{'Scenario':<22} {'Base':>10} {'Live':>10} {'Delta':>10} {'Worst Sleeve':>24}"
    )
    lines.append("-" * 70)

    for s in scenarios:
        lines.append(
            f"{s['scenario']:<22} "
            f"{s['base_impact_pct']:>9.2f}% "
            f"{s['live_impact_pct']:>9.2f}% "
            f"{s['overlay_delta_pct']:>9.2f}% "
            f"{s['worst_sleeve']:>24}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    report = load_scenario_report()
    scenarios = parse_scenario_results(report)

    print(format_scenario_table(scenarios))

    worst = find_worst_scenario(scenarios)
    best = find_best_scenario(scenarios)

    print("")
    print("WORST SCENARIO")
    print("-" * 70)
    print(worst)

    print("")
    print("BEST SCENARIO")
    print("-" * 70)
    print(best)