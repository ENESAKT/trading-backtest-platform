CREATE TABLE IF NOT EXISTS providers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    provider_type VARCHAR(50) NOT NULL,
    is_configured BOOLEAN DEFAULT FALSE,
    is_licensed BOOLEAN DEFAULT FALSE,
    supports_bist BOOLEAN DEFAULT FALSE,
    supports_viop BOOLEAN DEFAULT FALSE,
    supports_intraday BOOLEAN DEFAULT FALSE,
    max_history_days_json JSON,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingest_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    timeframe VARCHAR(50) NOT NULL,
    target_start_ts DATETIME,
    target_end_ts DATETIME,
    status VARCHAR(50) NOT NULL,
    attempt_count INT DEFAULT 0,
    rows_read INT DEFAULT 0,
    rows_written INT DEFAULT 0,
    started_at DATETIME,
    finished_at DATETIME,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);