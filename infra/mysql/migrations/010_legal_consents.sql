-- ============================================================
-- Migration 010 — Legal Consent + KVKK Account Controls
-- Yasal onay kayıtları, pazarlama onayı ve hesap silme/anonymize alanları
-- ============================================================

ALTER TABLE users
    ADD COLUMN marketing_consent BOOLEAN DEFAULT FALSE,
    ADD COLUMN marketing_consent_at DATETIME NULL,
    ADD COLUMN deleted_at DATETIME NULL,
    ADD COLUMN anonymized_at DATETIME NULL;

CREATE TABLE IF NOT EXISTS user_legal_consents (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    consent_type  VARCHAR(80) NOT NULL,
    accepted      BOOLEAN NOT NULL DEFAULT TRUE,
    version       VARCHAR(40) NOT NULL,
    text_snapshot TEXT,
    ip_address    VARCHAR(45),
    user_agent    VARCHAR(500),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ulc_user_id (user_id),
    INDEX idx_ulc_type (consent_type),
    INDEX idx_ulc_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

