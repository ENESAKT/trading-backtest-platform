CREATE TABLE IF NOT EXISTS data_retention_policy (
    id INT AUTO_INCREMENT PRIMARY KEY,
    market VARCHAR(50) NOT NULL,
    instrument_type VARCHAR(50) NOT NULL,
    timeframe VARCHAR(50) NOT NULL,
    retention_days INT NOT NULL,
    keep_raw BOOLEAN DEFAULT TRUE,
    keep_derived BOOLEAN DEFAULT TRUE,
    archive_before_delete BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_policy (market, instrument_type, timeframe)
);

-- Seed default policies based on planlama
INSERT IGNORE INTO data_retention_policy 
(market, instrument_type, timeframe, retention_days, archive_before_delete) VALUES
('BIST', 'stock', '1m', 365, FALSE),           -- 1 year
('BIST', 'stock', '5m', 3650, FALSE),          -- 10 years
('BIST', 'stock', '15m', 3650, FALSE),
('BIST', 'stock', '30m', 3650, FALSE),
('BIST', 'stock', '1h', 3650, FALSE),
('BIST', 'stock', '4h', 3650, FALSE),
('BIST', 'stock', '1d', 3650, FALSE),
('BIST', 'stock', '1w', 3650, FALSE),
('BIST', 'stock', '1mo', 3650, FALSE),
('BIST', 'stock', '1y', 3650, FALSE),
('VIOP', 'contract', '1m', 3650, FALSE),       -- 10 years for VIOP 1m
('VIOP', 'contract', '5m', 3650, FALSE);       -- 10 years for other VIOP
