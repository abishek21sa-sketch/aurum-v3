from pathlib import Path
import json


RESULTS_DIR = Path("results/factors")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    definitions = load_json(RESULTS_DIR / "factor_definitions.json")
    attribution = load_json(RESULTS_DIR / "factor_attribution_report.json")
    rotation = load_json(RESULTS_DIR / "factor_rotation_signal.json")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM INSTITUTIONAL FACTOR PLATFORM REPORT")
    lines.append("=" * 80)
    lines.append(f"Factor Count: {definitions['factor_count']}")
    lines.append(f"Regime:       {rotation['regime']}")
    lines.append(f"Posture:      {rotation['factor_posture']}")
    lines.append("")

    lines.append("FACTOR DEFINITIONS")
    lines.append("-" * 80)
    for factor in definitions["factors"]:
        lines.append(f"{factor['factor'].upper()}")
        lines.append(f"Description: {factor['description']}")
        lines.append(f"Logic:       {factor['economic_logic']}")
        lines.append(f"Risk:        {factor['risk']}")
        lines.append("")

    lines.append("FACTOR ATTRIBUTION")
    lines.append("-" * 80)
    for row in attribution["factor_attribution"]:
        lines.append(
            f"{row['factor'].upper():15} | "
            f"assets={row['asset_count']} | "
            f"{', '.join(row['assets'])}"
        )

    lines.append("")
    lines.append("FACTOR ROTATION SIGNAL")
    lines.append("-" * 80)
    lines.append(f"Preferred: {', '.join(rotation['preferred_factors'])}")
    lines.append(f"Avoid:     {', '.join(rotation['avoid_factors']) if rotation['avoid_factors'] else 'None'}")
    lines.append(f"View:      {rotation['interpretation']}")

    report = "\n".join(lines)

    (RESULTS_DIR / "factor_platform_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()