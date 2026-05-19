-- ============================================================
-- Migration 009 — Growth Tables
-- Waitlist, referral, affiliate, public backtest sharing
-- ============================================================

ALTER TABLE users
    ADD COLUMN referral_code VARCHAR(20) UNIQUE,
    ADD COLUMN referred_by BIGINT;

CREATE TABLE IF NOT EXISTS waitlist (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    email      VARCHAR(255) NOT NULL UNIQUE,
    source     VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS referral_rewards (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL,
    reward_type VARCHAR(50),
    granted_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (referred_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS affiliates (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT,
    code            VARCHAR(50) UNIQUE,
    commission_rate DECIMAL(5,2) DEFAULT 20.00,
    total_earnings  DECIMAL(10,2) DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public_backtests (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id      VARCHAR(100) NOT NULL,
    public_slug VARCHAR(50) NOT NULL UNIQUE,
    is_public   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_public_backtests_run_id (run_id)
);
