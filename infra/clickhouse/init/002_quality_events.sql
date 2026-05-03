CREATE TABLE IF NOT EXISTS data_quality_events
(
    id UUID DEFAULT generateUUIDv4(),
    market LowCardinality(String),
    symbol String,
    timeframe LowCardinality(String),
    event_type LowCardinality(String),
    start_ts DateTime64(3, 'UTC'),
    end_ts DateTime64(3, 'UTC'),
    severity LowCardinality(String),
    details_json String,
    detected_at DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(detected_at)
ORDER BY (market, symbol, timeframe, detected_at);