CREATE TABLE IF NOT EXISTS data_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    instrument_type VARCHAR(50),
    timeframe VARCHAR(50) NOT NULL,
    row_count BIGINT DEFAULT 0,
    first_ts DATETIME,
    last_ts DATETIME,
    target_start_ts DATETIME,
    target_end_ts DATETIME,
    coverage_pct DECIMAL(5,2) DEFAULT 0.00,
    storage_bytes BIGINT DEFAULT 0,
    raw_row_count BIGINT DEFAULT 0,
    derived_row_count BIGINT DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'not_configured',
    source VARCHAR(100),
    table_name VARCHAR(255),
    last_checked_at DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_market_symbol_timeframe (market, symbol, timeframe)
);

CREATE TABLE IF NOT EXISTS corporate_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    ex_date DATE NOT NULL,
    payable_date DATE,
    ratio DECIMAL(20,8),
    cash_amount DECIMAL(20,8),
    currency VARCHAR(10),
    source VARCHAR(100),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_date (symbol, ex_date)
);