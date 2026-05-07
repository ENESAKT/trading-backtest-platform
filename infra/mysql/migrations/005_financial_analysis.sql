CREATE TABLE IF NOT EXISTS financial_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    report_id VARCHAR(128) NOT NULL,
    period VARCHAR(32) NOT NULL,
    report_type VARCHAR(64) NOT NULL,
    source VARCHAR(100) NOT NULL,
    source_url TEXT,
    published_at DATETIME,
    quality_status VARCHAR(50) NOT NULL DEFAULT 'ok',
    raw_payload_json JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_financial_report (symbol, report_id),
    INDEX idx_symbol_period (symbol, period)
);

CREATE TABLE IF NOT EXISTS financial_statement_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    period VARCHAR(32) NOT NULL,
    statement_type VARCHAR(32) NOT NULL,
    item_key VARCHAR(160) NOT NULL,
    item_label VARCHAR(255) NOT NULL,
    value DECIMAL(24, 4),
    currency VARCHAR(10) DEFAULT 'TRY',
    source VARCHAR(100) NOT NULL,
    quality_status VARCHAR(50) NOT NULL DEFAULT 'ok',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_statement_item (symbol, period, statement_type, item_key),
    INDEX idx_symbol_statement_period (symbol, statement_type, period)
);

CREATE TABLE IF NOT EXISTS financial_ratios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    period VARCHAR(32) NOT NULL,
    ratio_key VARCHAR(120) NOT NULL,
    ratio_name VARCHAR(160) NOT NULL,
    value DECIMAL(24, 8),
    format VARCHAR(20) NOT NULL DEFAULT 'num',
    formula_version VARCHAR(32) NOT NULL DEFAULT 'v1',
    quality_status VARCHAR(50) NOT NULL DEFAULT 'ok',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ratio (symbol, period, ratio_key),
    INDEX idx_symbol_ratio_period (symbol, ratio_key, period)
);
