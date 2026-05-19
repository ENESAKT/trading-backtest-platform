-- Mali analiz: veri çekme log ve direktif/uyarı tabloları
-- Migration 006 — 2026-05-06

CREATE TABLE IF NOT EXISTS financial_fetch_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    fetch_type VARCHAR(50) NOT NULL DEFAULT 'quarterly',
    last_period VARCHAR(32),
    status VARCHAR(50) NOT NULL DEFAULT 'ok',
    periods_fetched INT DEFAULT 0,
    error_message TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ffl_symbol_type (symbol, fetch_type),
    INDEX idx_ffl_fetched_at (fetched_at)
);

CREATE TABLE IF NOT EXISTS financial_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(100),
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    period VARCHAR(32),
    metric_key VARCHAR(120),
    metric_value DECIMAL(24, 8),
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fa_symbol (symbol),
    INDEX idx_fa_alert_type (alert_type),
    INDEX idx_fa_created_at (created_at),
    INDEX idx_fa_is_read (is_read)
);

-- Ham DataFrame verisini satır olarak saklar (bilanço, gelir, nakit)
CREATE TABLE IF NOT EXISTS financial_raw_rows (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    period VARCHAR(32) NOT NULL,
    period_type VARCHAR(20) NOT NULL DEFAULT 'quarterly',
    statement_type VARCHAR(32) NOT NULL,
    row_index INT NOT NULL,
    label VARCHAR(255) NOT NULL,
    value DECIMAL(28, 4),
    currency VARCHAR(10) DEFAULT 'TRY',
    source VARCHAR(100) NOT NULL DEFAULT 'borsapy',
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_raw_row (symbol, period, statement_type, row_index),
    INDEX idx_frr_symbol_period (symbol, period),
    INDEX idx_frr_statement (symbol, statement_type, period)
);

-- Hesaplanmış oranlar (her çeyrek için)
CREATE TABLE IF NOT EXISTS financial_computed_ratios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    period VARCHAR(32) NOT NULL,
    ratio_key VARCHAR(100) NOT NULL,
    ratio_name VARCHAR(160) NOT NULL,
    value DECIMAL(28, 8),
    unit VARCHAR(20) DEFAULT 'x',
    category VARCHAR(50),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_computed_ratio (symbol, period, ratio_key),
    INDEX idx_cr_symbol_period (symbol, period),
    INDEX idx_cr_ratio_key (ratio_key, period)
);
