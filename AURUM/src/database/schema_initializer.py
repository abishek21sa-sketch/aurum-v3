from src.database.postgres_manager import PostgresManager


SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS market_ticks (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE market_ticks ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
ALTER TABLE market_ticks ADD COLUMN IF NOT EXISTS ticker TEXT;
ALTER TABLE market_ticks ADD COLUMN IF NOT EXISTS price DOUBLE PRECISION;
ALTER TABLE market_ticks ADD COLUMN IF NOT EXISTS volume DOUBLE PRECISION DEFAULT 0;
ALTER TABLE market_ticks ADD COLUMN IF NOT EXISTS source TEXT;
ALTER TABLE market_ticks ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}'::jsonb;
ALTER TABLE market_ticks ADD COLUMN IF NOT EXISTS time TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS market_features (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE market_features ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
ALTER TABLE market_features ADD COLUMN IF NOT EXISTS ticker TEXT;
ALTER TABLE market_features ADD COLUMN IF NOT EXISTS volatility DOUBLE PRECISION;
ALTER TABLE market_features ADD COLUMN IF NOT EXISTS momentum DOUBLE PRECISION;
ALTER TABLE market_features ADD COLUMN IF NOT EXISTS liquidity DOUBLE PRECISION;
ALTER TABLE market_features ADD COLUMN IF NOT EXISTS regime TEXT;
ALTER TABLE market_features ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}'::jsonb;
ALTER TABLE market_features ADD COLUMN IF NOT EXISTS time TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS market_signals (
    signal_id TEXT PRIMARY KEY
);

ALTER TABLE market_signals ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
ALTER TABLE market_signals ADD COLUMN IF NOT EXISTS signal_type TEXT;
ALTER TABLE market_signals ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION;
ALTER TABLE market_signals ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS portfolio_state (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE portfolio_state ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
ALTER TABLE portfolio_state ADD COLUMN IF NOT EXISTS portfolio_value DOUBLE PRECISION;
ALTER TABLE portfolio_state ADD COLUMN IF NOT EXISTS cash DOUBLE PRECISION;
ALTER TABLE portfolio_state ADD COLUMN IF NOT EXISTS risk_budget DOUBLE PRECISION;
ALTER TABLE portfolio_state ADD COLUMN IF NOT EXISTS regime TEXT;
ALTER TABLE portfolio_state ADD COLUMN IF NOT EXISTS health TEXT;
ALTER TABLE portfolio_state ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS portfolio_decisions (
    decision_id TEXT PRIMARY KEY
);

ALTER TABLE portfolio_decisions ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
ALTER TABLE portfolio_decisions ADD COLUMN IF NOT EXISTS action TEXT;
ALTER TABLE portfolio_decisions ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION;
ALTER TABLE portfolio_decisions ADD COLUMN IF NOT EXISTS rationale TEXT;
ALTER TABLE portfolio_decisions ADD COLUMN IF NOT EXISTS execution_permission TEXT;
ALTER TABLE portfolio_decisions ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS committee_decisions (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE committee_decisions ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
ALTER TABLE committee_decisions ADD COLUMN IF NOT EXISTS investment_view TEXT;
ALTER TABLE committee_decisions ADD COLUMN IF NOT EXISTS approval_status TEXT;
ALTER TABLE committee_decisions ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION;
ALTER TABLE committee_decisions ADD COLUMN IF NOT EXISTS minutes TEXT;
ALTER TABLE committee_decisions ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS execution_log (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE execution_log ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
ALTER TABLE execution_log ADD COLUMN IF NOT EXISTS ticker TEXT;
ALTER TABLE execution_log ADD COLUMN IF NOT EXISTS side TEXT;
ALTER TABLE execution_log ADD COLUMN IF NOT EXISTS quantity DOUBLE PRECISION;
ALTER TABLE execution_log ADD COLUMN IF NOT EXISTS price DOUBLE PRECISION;
ALTER TABLE execution_log ADD COLUMN IF NOT EXISTS status TEXT;
ALTER TABLE execution_log ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS learning_events (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE learning_events ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
ALTER TABLE learning_events ADD COLUMN IF NOT EXISTS event_type TEXT;
ALTER TABLE learning_events ADD COLUMN IF NOT EXISTS lesson TEXT;
ALTER TABLE learning_events ADD COLUMN IF NOT EXISTS outcome TEXT;
ALTER TABLE learning_events ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_market_ticks_ticker_time
ON market_ticks (ticker, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_market_features_ticker_time
ON market_features (ticker, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_market_signals_time
ON market_signals (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_portfolio_state_time
ON portfolio_state (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_portfolio_decisions_time
ON portfolio_decisions (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_committee_decisions_time
ON committee_decisions (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_execution_log_time
ON execution_log (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_learning_events_time
ON learning_events (timestamp DESC);
"""


HYPERTABLE_SQL = """
SELECT create_hypertable('market_ticks', 'timestamp', if_not_exists => TRUE);
SELECT create_hypertable('market_features', 'timestamp', if_not_exists => TRUE);
"""


class SchemaInitializer:
    def __init__(self, db: PostgresManager | None = None):
        self.db = db or PostgresManager()

    def initialize(self) -> None:
        self.db.execute(SCHEMA_SQL)

        try:
            self.db.execute(HYPERTABLE_SQL)
        except Exception as exc:
            print(f"[WARN] Timescale hypertable setup skipped: {exc}")

    def table_exists(self, table_name: str) -> bool:
        row = self.db.fetch_one(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            ) AS exists;
            """,
            (table_name,),
        )
        return bool(row and row["exists"])