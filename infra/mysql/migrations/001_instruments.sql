CREATE TABLE IF NOT EXISTS instruments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    display_symbol VARCHAR(100),
    instrument_type VARCHAR(50),
    isin VARCHAR(50),
    company_name VARCHAR(255),
    sector VARCHAR(100),
    exchange VARCHAR(100),
    currency VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    first_seen_at DATETIME,
    delisted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_market_symbol (market, symbol)
);

CREATE TABLE IF NOT EXISTS viop_contracts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contract_symbol VARCHAR(100) NOT NULL,
    underlying_symbol VARCHAR(100) NOT NULL,
    contract_type VARCHAR(50),
    maturity DATE,
    active_from DATETIME,
    active_to DATETIME,
    rollover_group VARCHAR(50),
    previous_contract_symbol VARCHAR(100),
    next_contract_symbol VARCHAR(100),
    multiplier DECIMAL(20,8),
    tick_size DECIMAL(20,8),
    currency VARCHAR(10),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_contract_symbol (contract_symbol)
);