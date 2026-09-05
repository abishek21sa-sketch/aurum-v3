from pathlib import Path
import pandas as pd


class LiveSignalEngine:
    def __init__(
        self,
        snapshot_path="data/live/live_market_snapshot.csv",
        returns_path="data/live/live_market_return_snapshot.csv",
        output_path="data/live/live_signal_snapshot.csv",
    ):
        self.snapshot_path = Path(snapshot_path)
        self.returns_path = Path(returns_path)
        self.output_path = Path(output_path)

    def run(self):
        snapshot = pd.read_csv(self.snapshot_path)
        returns = pd.read_csv(self.returns_path)

        row = returns.iloc[0]

        equity_return = row[["SPY", "QQQ", "DIA"]].mean()
        defensive_return = row[["TLT", "GLD"]].mean()
        crypto_return = row[["BTC-USD", "ETH-USD"]].mean()
        vix_return = row["VIX"]

        risk_on_score = equity_return - defensive_return
        defensive_score = defensive_return - equity_return
        crypto_stress = -crypto_return if crypto_return < 0 else 0
        volatility_stress = vix_return if vix_return > 0 else 0

        if risk_on_score > 0.003 and volatility_stress == 0:
            hedge_posture = "RISK_ON"
        elif defensive_score > 0.003 or crypto_stress > 0.02 or volatility_stress > 0.03:
            hedge_posture = "DEFENSIVE"
        else:
            hedge_posture = "NEUTRAL"

        if hedge_posture == "RISK_ON":
            interpretation = (
                "Equity leadership is positive and volatility pressure is contained."
            )
        elif hedge_posture == "DEFENSIVE":
            interpretation = (
                "Market conditions show defensive pressure or stress in risk assets."
            )
        else:
            interpretation = (
                "Market conditions are mixed with no decisive live allocation signal."
            )

        signal = pd.DataFrame([{
            "Date": row["Date"],
            "equity_return": equity_return,
            "defensive_return": defensive_return,
            "crypto_return": crypto_return,
            "vix_return": vix_return,
            "risk_on_score": risk_on_score,
            "defensive_score": defensive_score,
            "crypto_stress": crypto_stress,
            "volatility_stress": volatility_stress,
            "hedge_posture": hedge_posture,
            "interpretation": interpretation,
        }])

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        signal.to_csv(self.output_path, index=False)

        print("LIVE SIGNAL ENGINE COMPLETE")
        print("=" * 70)
        print(signal.to_string(index=False))
        print()
        print(f"Saved signal snapshot: {self.output_path}")

        return signal


if __name__ == "__main__":
    engine = LiveSignalEngine()
    engine.run()