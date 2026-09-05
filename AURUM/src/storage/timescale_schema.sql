CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS market_ticks (
    time TIMESTAMPTZ NOT NULL,
    redis_id TEXT,
    event_type TEXT,
    source TEXT,
    ticker TEXT NOT NULL,
    price DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    ingested_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS market_features (
    time TIMESTAMPTZ NOT NULL,
    redis_id TEXT,
    event_type TEXT,
    ticker TEXT NOT NULL,
    source TEXT,
    price DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    return_1m DOUBLE PRECISION,
    return_5m DOUBLE PRECISION,
    rolling_volatility DOUBLE PRECISION,
    momentum DOUBLE PRECISION,
    volume_zscore DOUBLE PRECISION,
    liquidity_state TEXT,
    volatility_state TEXT,
    history_size INTEGER,
    computed_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS realtime_alerts (
    time TIMESTAMPTZ NOT NULL,
    redis_id TEXT,
    event_type TEXT,
    alert_id TEXT,
    alert_type TEXT,
    ticker TEXT NOT NULL,
    severity TEXT,
    severity_rank INTEGER,
    message TEXT,
    metric_name TEXT,
    metric_value DOUBLE PRECISION,
    threshold DOUBLE PRECISION,
    price DOUBLE PRECISION,
    source_event_timestamp TIMESTAMPTZ,
    computed_at TIMESTAMPTZ,
    alerted_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ
);

SELECT create_hypertable('market_ticks', 'time', if_not_exists => TRUE);
SELECT create_hypertable('market_features', 'time', if_not_exists => TRUE);
SELECT create_hypertable('realtime_alerts', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_market_ticks_ticker_time
ON market_ticks (ticker, time DESC);

CREATE INDEX IF NOT EXISTS idx_market_features_ticker_time
ON market_features (ticker, time DESC);

CREATE INDEX IF NOT EXISTS idx_realtime_alerts_ticker_time
ON realtime_alerts (ticker, time DESC);

CREATE INDEX IF NOT EXISTS idx_realtime_alerts_severity_time
ON realtime_alerts (severity, time DESC);