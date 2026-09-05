from datetime import datetime, timezone
from uuid import uuid4

from src.database.postgres_manager import PostgresManager


def utc_now():
    return datetime.now(timezone.utc)


class MarketRepository:
    def __init__(self, db: PostgresManager | None = None):
        self.db = db or PostgresManager()

    def insert_tick(
        self,
            ticker: str,
            price: float,
            volume: float = 0.0,
            source: str = "unknown",
            timestamp=None,
            payload: dict | None = None,
        ) -> None:
            ts = timestamp or utc_now()

            self.db.execute(
                """
                INSERT INTO market_ticks
                (time, timestamp, ticker, price, volume, source, payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    ts,
                    ts,
                    ticker,
                    price,
                    volume,
                    source,
                    self.db.json(payload or {}),
                ),
            )

    def insert_feature(
        self,
        ticker: str,
        volatility: float | None = None,
        momentum: float | None = None,
        liquidity: float | None = None,
        regime: str | None = None,
        timestamp=None,
        payload: dict | None = None,
    ) -> None:
        ts = timestamp or utc_now()

        self.db.execute(
            """
            INSERT INTO market_features
            (time, timestamp, ticker, volatility, momentum, liquidity, regime, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                ts,
                ts,
                ticker,
                volatility,
                momentum,
                liquidity,
                regime,
                self.db.json(payload or {}),
            ),
        )

    def insert_signal(
        self,
        signal_type: str,
        confidence: float,
        timestamp=None,
        payload: dict | None = None,
        signal_id: str | None = None,
    ) -> str:
        sid = signal_id or f"signal_{uuid4().hex[:12]}"

        self.db.execute(
            """
            INSERT INTO market_signals
            (signal_id, timestamp, signal_type, confidence, payload)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (signal_id) DO UPDATE
            SET timestamp = EXCLUDED.timestamp,
                signal_type = EXCLUDED.signal_type,
                confidence = EXCLUDED.confidence,
                payload = EXCLUDED.payload;
            """,
            (
                sid,
                timestamp or utc_now(),
                signal_type,
                confidence,
                self.db.json(payload or {}),
            ),
        )

        return sid