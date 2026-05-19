CREATE TABLE IF NOT EXISTS viop_contracts (
    symbol String,
    contract_type String,
    maturity Date,
    underlying String,
    is_active UInt8,
    rollover_at DateTime64(3, 'UTC'),
    source String,
    _ingested_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (contract_type, maturity, symbol);

CREATE TABLE IF NOT EXISTS viop_bars (
    symbol String,
    contract_type String,
    maturity Date,
    interval String,
    ts DateTime64(3, 'UTC'),
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    open_interest Float64,
    source String,
    is_real Bool,
    _ingested_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY (toYYYYMM(ts), contract_type)
ORDER BY (symbol, interval, ts)
TTL ts + INTERVAL 10 YEAR;
