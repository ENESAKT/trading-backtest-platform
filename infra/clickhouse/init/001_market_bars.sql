CREATE TABLE IF NOT EXISTS market_bars
(
    market LowCardinality(String),
    symbol String,
    instrument_type LowCardinality(String),
    timeframe LowCardinality(String),
    ts DateTime64(3, 'UTC'),
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    source LowCardinality(String),
    source_timeframe LowCardinality(String),
    is_derived UInt8,
    quality_status LowCardinality(String),
    ingest_job_id String,
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY (market, timeframe, toYYYYMM(ts))
ORDER BY (market, symbol, timeframe, ts);