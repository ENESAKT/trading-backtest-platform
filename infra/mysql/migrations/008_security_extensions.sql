-- ============================================================
-- Migration 008 — Security Extensions
-- TOTP, API keys, webhook idempotency, migration tracking
-- ============================================================

ALTER TABLE users
    ADD COLUMN totp_secret VARCHAR(64),
    ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS api_keys (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    name       VARCHAR(100),
    key_hash   VARCHAR(255) NOT NULL,
    last_used  DATETIME,
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_api_keys_user_id (user_id),
    UNIQUE KEY uk_api_key_hash (key_hash),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS webhook_events (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider     VARCHAR(50) NOT NULL DEFAULT 'stripe',
    event_id     VARCHAR(255) NOT NULL,
    event_type   VARCHAR(100) NOT NULL,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_webhook_event (provider, event_id)
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version    VARCHAR(255) PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
