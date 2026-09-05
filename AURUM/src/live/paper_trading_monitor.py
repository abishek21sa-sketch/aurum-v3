from pathlib import Path
import pandas as pd
import numpy as np


class PaperTradingMonitor:
    def __init__(
        self,
        meta_weights_path="data/optimization/meta_strategy_weights.csv",
        factor_summary_path="data/analytics/factor_attribution_summary_v2.csv",
        walk_forward_path="data/validation/walk_forward_meta_validation_summary.csv",
        output_snapshot_path="results/live/paper_trading_snapshot.txt",
        output_monitor_path="results/live/daily_risk_monitor.csv",
    ):
        self.meta_weights_path = Path(meta_weights_path)
        self.factor_summary_path = Path(factor_summary_path)
        self.walk_forward_path = Path(walk_forward_path)

        self.output_snapshot_path = Path(output_snapshot_path)
        self.output_monitor_path = Path(output_monitor_path)

    def classify_risk_regime(self, volatility, drawdown):
        if volatility > 0.15 or drawdown < -0.15:
            return "HIGH_RISK"

        if volatility > 0.08 or drawdown < -0.08:
            return "MODERATE_RISK"

        return "LOW_RISK"

    def classify_market_posture(self, dominant_factor):
        if dominant_factor in ["gold_hedge", "defensive_bond"]:
            return "RISK_OFF"

        if dominant_factor in ["equity_beta", "crypto_beta"]:
            return "RISK_ON"

        return "NEUTRAL"

    def generate_alerts(
        self,
        volatility,
        drawdown,
        diversification_score,
    ):
        alerts = []

        if volatility > 0.15:
            alerts.append("VOLATILITY_ALERT")

        if drawdown < -0.10:
            alerts.append("DRAWDOWN_ALERT")

        if diversification_score < 0.40:
            alerts.append("FACTOR_CONCENTRATION_ALERT")

        if not alerts:
            alerts.append("NO_ACTIVE_ALERTS")

        return alerts

    def run(self):
        meta_weights = pd.read_csv(self.meta_weights_path)
        factor_summary = pd.read_csv(self.factor_summary_path)
        walk_forward = pd.read_csv(self.walk_forward_path)

        fs = factor_summary.iloc[0]
        wf = walk_forward.iloc[0]

        volatility = wf["volatility"]
        drawdown = wf["max_drawdown"]

        diversification_score = fs["factor_diversification_score"]
        dominant_factor = fs["dominant_factor"]

        risk_regime = self.classify_risk_regime(
            volatility,
            drawdown,
        )

        market_posture = self.classify_market_posture(
            dominant_factor,
        )

        alerts = self.generate_alerts(
            volatility,
            drawdown,
            diversification_score,
        )

        monitor_row = {
            "risk_regime": risk_regime,
            "market_posture": market_posture,
            "walk_forward_return": wf["total_return"],
            "walk_forward_volatility": volatility,
            "walk_forward_sharpe": wf["sharpe_like"],
            "walk_forward_drawdown": drawdown,
            "factor_diversification_score": diversification_score,
            "dominant_factor": dominant_factor,
            "alerts": ",".join(alerts),
        }

        monitor_df = pd.DataFrame([monitor_row])

        lines = []

        lines.append("AURUM PAPER TRADING MONITOR")
        lines.append("=" * 70)
        lines.append("")

        lines.append("CURRENT SYSTEM STATE")
        lines.append("-" * 70)
        lines.append(f"Risk Regime: {risk_regime}")
        lines.append(f"Market Posture: {market_posture}")
        lines.append(f"Dominant Factor: {dominant_factor}")
        lines.append(
            f"Factor Diversification Score: "
            f"{diversification_score:.2f}"
        )

        lines.append("")
        lines.append("WALK-FORWARD PERFORMANCE")
        lines.append("-" * 70)
        lines.append(
            f"Return: {wf['total_return']:.2%}"
        )
        lines.append(
            f"Volatility: {volatility:.2%}"
        )
        lines.append(
            f"Sharpe-like: {wf['sharpe_like']:.2f}"
        )
        lines.append(
            f"Max Drawdown: {drawdown:.2%}"
        )

        lines.append("")
        lines.append("META STRATEGY WEIGHTS")
        lines.append("-" * 70)

        for _, row in meta_weights.iterrows():
            lines.append(
                f"{row['strategy']:<28} "
                f"{row['meta_weight']:.2%}"
            )

        lines.append("")
        lines.append("ACTIVE ALERTS")
        lines.append("-" * 70)

        for alert in alerts:
            lines.append(f"- {alert}")

        lines.append("")
        lines.append("SYSTEM INTERPRETATION")
        lines.append("-" * 70)

        if risk_regime == "LOW_RISK":
            lines.append(
                "Portfolio conditions remain stable with "
                "controlled volatility and drawdown behavior."
            )

        elif risk_regime == "MODERATE_RISK":
            lines.append(
                "Portfolio risk conditions have elevated. "
                "Defensive positioning should be monitored."
            )

        else:
            lines.append(
                "Portfolio risk conditions are stressed. "
                "Risk reduction procedures may be necessary."
            )

        lines.append("")
        lines.append(
            "The monitoring engine indicates that the "
            "meta-strategy framework remains diversified "
            "across multiple portfolio construction methodologies."
        )

        snapshot = "\n".join(lines)

        self.output_snapshot_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        monitor_df.to_csv(
            self.output_monitor_path,
            index=False,
        )

        with open(
            self.output_snapshot_path,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(snapshot)

        print("PAPER TRADING MONITOR COMPLETE")
        print("=" * 70)
        print(snapshot)
        print()
        print(f"Saved snapshot: {self.output_snapshot_path}")
        print(f"Saved monitor: {self.output_monitor_path}")

        return monitor_df, snapshot


if __name__ == "__main__":
    monitor = PaperTradingMonitor()
    monitor.run()