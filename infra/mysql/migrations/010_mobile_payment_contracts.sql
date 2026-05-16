-- ============================================================
-- Migration 010 — Mobile auth + payment webhook contract fixes
-- Safe follow-up for databases that already applied 008.
-- ============================================================

ALTER TABLE refresh_tokens
    ADD COLUMN jti VARCHAR(64),
    ADD INDEX idx_rt_jti (jti);

CREATE TABLE IF NOT EXISTS webhook_events (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider     VARCHAR(50) NOT NULL DEFAULT 'stripe',
    event_id     VARCHAR(255) NOT NULL,
    event_type   VARCHAR(100) NOT NULL,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_webhook_event (provider, event_id)
);
