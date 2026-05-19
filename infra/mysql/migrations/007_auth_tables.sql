-- ============================================================
-- Migration 007 — Auth + Abonelik Tabloları
-- PiyasaPilot kullanıcı, oturum, plan ve abonelik altyapısı
-- ============================================================

-- ─── Kullanıcılar ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    email          VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash  VARCHAR(255),              -- NULL = sadece OAuth
    display_name   VARCHAR(100),
    avatar_url     VARCHAR(500),
    role           ENUM('guest','free','pro','ultra','admin') DEFAULT 'free',
    language       ENUM('tr','en') DEFAULT 'tr',
    is_active      BOOLEAN DEFAULT TRUE,
    last_login_at  DATETIME,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_email (email)
);

-- ─── Google / OAuth Hesapları ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS oauth_accounts (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id          BIGINT NOT NULL,
    provider         VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    access_token     TEXT,
    refresh_token    TEXT,
    expires_at       DATETIME,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_provider_user (provider, provider_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Refresh Token Deposu ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    token_hash  VARCHAR(255) NOT NULL,
    jti         VARCHAR(64),                  -- JWT ID — blacklist için
    user_agent  VARCHAR(500),
    ip_address  VARCHAR(45),
    device_name VARCHAR(100),
    expires_at  DATETIME NOT NULL,
    revoked_at  DATETIME,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rt_user_id (user_id),
    INDEX idx_rt_token_hash (token_hash),
    INDEX idx_rt_jti (jti),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Email Doğrulama Tokenları ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at    DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_evt_token (token_hash),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Şifre Sıfırlama Tokenları ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at    DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prt_token (token_hash),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Kullanıcı Ayarları (JSON) ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_settings (
    user_id            BIGINT PRIMARY KEY,
    favorite_symbols   JSON,
    default_symbol     VARCHAR(50) DEFAULT 'BTCUSDT',
    default_timeframe  VARCHAR(10) DEFAULT '1h',
    theme              ENUM('dark','light') DEFAULT 'dark',
    accent_color       VARCHAR(20) DEFAULT 'amber',
    notification_prefs JSON,
    dashboard_layout   JSON,
    onboarding_done    BOOLEAN DEFAULT FALSE,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Abonelik Planları ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subscription_plans (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    slug                    VARCHAR(50) NOT NULL UNIQUE,
    display_name_tr         VARCHAR(100) NOT NULL,
    display_name_en         VARCHAR(100) NOT NULL,
    price_monthly_usd       DECIMAL(10,2) DEFAULT 0,
    price_yearly_usd        DECIMAL(10,2) DEFAULT 0,
    stripe_monthly_price_id VARCHAR(100),
    stripe_yearly_price_id  VARCHAR(100),
    api_calls_per_day       INT DEFAULT 500,       -- -1 = sınırsız
    backtest_runs_per_day   INT DEFAULT 5,          -- -1 = sınırsız
    max_watchlist_symbols   INT DEFAULT 10,         -- -1 = sınırsız
    max_paper_accounts      INT DEFAULT 1,          -- -1 = sınırsız
    max_chart_templates     INT DEFAULT 1,          -- -1 = sınırsız
    signals_per_day         INT DEFAULT 3,          -- -1 = sınırsız
    real_time_data          BOOLEAN DEFAULT FALSE,
    backtest_pro_enabled    BOOLEAN DEFAULT FALSE,
    scanner_enabled         BOOLEAN DEFAULT FALSE,
    mali_analiz_scope       ENUM('none','bist30','bist100','all') DEFAULT 'bist30',
    education_full          BOOLEAN DEFAULT FALSE,
    telegram_bot            BOOLEAN DEFAULT FALSE,
    api_access              BOOLEAN DEFAULT FALSE,
    multi_chart             BOOLEAN DEFAULT FALSE,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Kullanıcı Abonelikleri ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id                     BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id                BIGINT NOT NULL,
    plan_id                INT NOT NULL,
    stripe_subscription_id VARCHAR(100),
    stripe_customer_id     VARCHAR(100),
    billing_period         ENUM('monthly','yearly') DEFAULT 'monthly',
    status                 ENUM('trialing','active','cancelled','expired','past_due') DEFAULT 'active',
    trial_ends_at          DATETIME,
    current_period_start   DATETIME,
    current_period_end     DATETIME,
    cancelled_at           DATETIME,
    created_at             DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at             DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_us_user_id (user_id),
    INDEX idx_us_stripe_sub (stripe_subscription_id),
    UNIQUE KEY uk_us_stripe_sub (stripe_subscription_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
);

-- ─── Günlük Kullanım Sayaçları ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_usage (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    date          DATE NOT NULL,
    api_calls     INT DEFAULT 0,
    backtest_runs INT DEFAULT 0,
    signal_views  INT DEFAULT 0,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_date (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Denetim Logu ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT,
    action     VARCHAR(100) NOT NULL,
    resource   VARCHAR(200),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    metadata   JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_al_user_id (user_id),
    INDEX idx_al_action (action),
    INDEX idx_al_created_at (created_at)
);

-- ─── Stripe Webhook İdempotency ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stripe_events (
    id         VARCHAR(100) PRIMARY KEY,    -- Stripe event_id
    type       VARCHAR(100) NOT NULL,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_se_type (type)
);

-- ─── Başlangıç Planları (seed) ───────────────────────────────────────────────
INSERT IGNORE INTO subscription_plans
    (slug, display_name_tr, display_name_en,
     price_monthly_usd, price_yearly_usd,
     api_calls_per_day, backtest_runs_per_day,
     max_watchlist_symbols, max_paper_accounts, max_chart_templates,
     signals_per_day,
     real_time_data, backtest_pro_enabled, scanner_enabled,
     mali_analiz_scope, education_full, telegram_bot, api_access, multi_chart)
VALUES
    ('free',  'Ücretsiz', 'Free',
      0.00,   0.00,
       500,   5,  10, 1,  1,   3,
     FALSE, FALSE, FALSE, 'bist30',  FALSE, FALSE, FALSE, FALSE),

    ('pro',   'Pro',      'Pro',
      19.99, 199.99,
      5000,  50,  50, 5, 10,  -1,
     FALSE, TRUE,  TRUE,  'bist100', TRUE,  TRUE,  FALSE, TRUE),

    ('ultra', 'Ultra',    'Ultra',
      49.99, 499.99,
     -1,    -1,  -1, -1, -1,  -1,
     TRUE,  TRUE,  TRUE,  'all',     TRUE,  TRUE,  TRUE,  TRUE);
-- Not: -1 = sınırsız
