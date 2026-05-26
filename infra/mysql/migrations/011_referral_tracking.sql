-- ============================================================
-- Migration 011 — Referral Tracking (Bölüm 17)
-- growth_router.py referral sistemi için gerekli tablolar.
-- ============================================================

-- Kullanıcı başına referral kodu (users tablosundaki referral_code'un
-- daha yapılandırılmış hali; eski sütun bırakılır geriye dönük uyum için)
CREATE TABLE IF NOT EXISTS referral_codes (
    id         BIGINT       AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT       NOT NULL UNIQUE,
    code       VARCHAR(16)  NOT NULL UNIQUE,
    created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_referral_codes_code (code),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Her referral tıklaması ve conversion olayı
CREATE TABLE IF NOT EXISTS referral_events (
    id         BIGINT       AUTO_INCREMENT PRIMARY KEY,
    code       VARCHAR(16)  NOT NULL,
    event_type ENUM('click','conversion') NOT NULL,
    ip_hash    VARCHAR(64)  DEFAULT NULL,   -- isteğe bağlı fraud koruması
    created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_referral_events_code       (code),
    INDEX idx_referral_events_code_type  (code, event_type),
    INDEX idx_referral_events_created_at (created_at)
);

-- Verilen ödüller (her (user_id, reward_type, code) için yalnızca bir kayıt)
DROP TABLE IF EXISTS referral_rewards;   -- 009 migrationdaki basit sürümü kaldır
CREATE TABLE IF NOT EXISTS referral_rewards (
    id          BIGINT       AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT       NOT NULL,    -- ödül alan kullanıcı (referrer)
    code        VARCHAR(16)  NOT NULL,
    reward_type VARCHAR(50)  NOT NULL,
    granted_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY uk_referral_rewards_unique (user_id, reward_type, code),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Waitlist tablosuna ref_code ve joined_at sütunlarını ekle
ALTER TABLE waitlist
    ADD COLUMN IF NOT EXISTS ref_code  VARCHAR(16)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS joined_at DATETIME(6)  DEFAULT CURRENT_TIMESTAMP(6);
