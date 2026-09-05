from pathlib import Path
import pandas as pd


class LiveAllocationOverlay:
    def __init__(
        self,
        meta_weights_path="data/optimization/meta_strategy_weights.csv",
        live_signal_path="data/live/live_signal_snapshot.csv",
        output_csv_path="data/live/live_allocation_overlay.csv",
        output_txt_path="results/live/live_allocation_overlay.txt",
    ):
        self.meta_weights_path = Path(meta_weights_path)
        self.live_signal_path = Path(live_signal_path)
        self.output_csv_path = Path(output_csv_path)
        self.output_txt_path = Path(output_txt_path)

    def adjustment_multiplier(self, strategy, hedge_posture):
        if hedge_posture == "RISK_ON":
            multipliers = {
                "black_litterman": 1.25,
                "bayesian_robust": 1.10,
                "dynamic_allocation": 1.05,
                "rolling_min_variance": 0.95,
                "regime_aware": 0.95,
                "hrp": 0.95,
            }

        elif hedge_posture == "DEFENSIVE":
            multipliers = {
                "black_litterman": 0.75,
                "bayesian_robust": 1.15,
                "dynamic_allocation": 1.00,
                "rolling_min_variance": 1.15,
                "regime_aware": 1.15,
                "hrp": 1.10,
            }

        else:
            multipliers = {
                "black_litterman": 1.00,
                "bayesian_robust": 1.00,
                "dynamic_allocation": 1.00,
                "rolling_min_variance": 1.00,
                "regime_aware": 1.00,
                "hrp": 1.00,
            }

        return multipliers.get(strategy, 1.00)

    def run(self):
        meta_weights = pd.read_csv(self.meta_weights_path)
        signal = pd.read_csv(self.live_signal_path).iloc[0]

        hedge_posture = signal["hedge_posture"]

        adjusted = meta_weights.copy()

        adjusted["live_multiplier"] = adjusted["strategy"].apply(
            lambda strategy: self.adjustment_multiplier(
                strategy,
                hedge_posture,
            )
        )

        adjusted["raw_live_weight"] = (
            adjusted["meta_weight"] * adjusted["live_multiplier"]
        )

        adjusted["live_weight"] = (
            adjusted["raw_live_weight"]
            / adjusted["raw_live_weight"].sum()
        )

        adjusted["weight_change"] = (
            adjusted["live_weight"] - adjusted["meta_weight"]
        )

        self.output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_txt_path.parent.mkdir(parents=True, exist_ok=True)

        adjusted.to_csv(self.output_csv_path, index=False)

        lines = []

        lines.append("AURUM LIVE ALLOCATION OVERLAY")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Live Hedge Posture: {hedge_posture}")
        lines.append(f"Live Signal Date: {signal['Date']}")
        lines.append("")
        lines.append("LIVE STRATEGY WEIGHT ADJUSTMENTS")
        lines.append("-" * 70)

        for _, row in adjusted.iterrows():
            lines.append(
                f"{row['strategy']:<28} "
                f"Base: {row['meta_weight']:.2%} | "
                f"Live: {row['live_weight']:.2%} | "
                f"Change: {row['weight_change']:+.2%}"
            )

        lines.append("")
        lines.append("LIVE INTERPRETATION")
        lines.append("-" * 70)

        if hedge_posture == "RISK_ON":
            lines.append(
                "Live conditions favor modestly increasing tactical "
                "return-seeking sleeves while slightly reducing defensive "
                "allocators."
            )

        elif hedge_posture == "DEFENSIVE":
            lines.append(
                "Live conditions favor defensive positioning with higher "
                "allocation toward robust and stability-oriented strategies."
            )

        else:
            lines.append(
                "Live conditions are mixed, so the system keeps baseline "
                "meta-strategy weights mostly unchanged."
            )

        report = "\n".join(lines)

        with open(self.output_txt_path, "w", encoding="utf-8") as f:
            f.write(report)

        print("LIVE ALLOCATION OVERLAY COMPLETE")
        print("=" * 70)
        print(report)
        print()
        print(f"Saved overlay CSV: {self.output_csv_path}")
        print(f"Saved overlay report: {self.output_txt_path}")

        return adjusted, report


if __name__ == "__main__":
    overlay = LiveAllocationOverlay()
    overlay.run()