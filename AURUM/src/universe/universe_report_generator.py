from pathlib import Path
import json


RESULTS_DIR = Path("results/universe")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    summary = load_json(RESULTS_DIR / "universe_summary.json")
    breakdown = load_json(RESULTS_DIR / "asset_class_breakdown.json")

    lines = []
    lines.append("=" * 80)
    lines.append("AURUM MULTI-ASSET UNIVERSE REPORT")
    lines.append("=" * 80)
    lines.append(f"Universe: {summary['universe_name']}")
    lines.append(f"Assets:   {summary['asset_count']}")
    lines.append("")

    for asset_class, assets in breakdown.items():
        lines.append(asset_class.upper())
        lines.append("-" * 80)
        for asset in assets:
            lines.append(
                f"{asset['ticker']:10} | {asset['name']} | "
                f"role={asset['role']} | provider={asset['data_provider_symbol']}"
            )
        lines.append("")

    report = "\n".join(lines)

    (RESULTS_DIR / "universe_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()