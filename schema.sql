-- ============================================================
-- Telegram Bot Sandbox Demo Database Schema
-- STRICT BOUNDARY: Local test simulation only (is_demo=TRUE)
-- ============================================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    balance BIGINT DEFAULT 50000, -- 50 000 demo UZS initial sandbox balance
    total_deposit BIGINT DEFAULT 0,
    referral_id BIGINT NULL,
    referral_count INTEGER DEFAULT 0,
    is_banned BOOLEAN DEFAULT FALSE,
    is_demo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_referral_count ON users(referral_count DESC);

-- 2. CHANNELS TABLE (Demo Channels)
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    link TEXT NOT NULL,
    username TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. SERVICES TABLE (Demo Services with is_demo=TRUE)
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    platform TEXT NOT NULL, -- Telegram, Instagram, YouTube, TikTok
    category TEXT NOT NULL, -- Reaksiya, Ko'rishlar, Obunachi, Boost ovoz, Hikoya, O'zbek tarmoq
    service_id_external INTEGER,
    name TEXT NOT NULL,
    price_per_1000 BIGINT NOT NULL, -- Price in UZS
    min_order INTEGER NOT NULL DEFAULT 10,
    max_order INTEGER NOT NULL DEFAULT 100000,
    description TEXT DEFAULT 'DEMO MODE — Faqat test simulyatsiyasi',
    estimated_time TEXT DEFAULT '1-5 daqiqa (Demo)',
    is_free BOOLEAN DEFAULT FALSE,
    is_demo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_services_platform_cat ON services(platform, category);

-- 4. ORDERS TABLE (Strict is_demo enforcement)
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL,
    service_id INTEGER REFERENCES services(id) ON DELETE SET NULL,
    service_name TEXT,
    link TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price BIGINT NOT NULL,
    status TEXT DEFAULT 'demo_processing', -- demo_pending, demo_paid, demo_processing, demo_completed, demo_cancelled
    estimated_time TEXT DEFAULT '1-5 daqiqa (Demo)',
    is_demo BOOLEAN NOT NULL DEFAULT TRUE,
    external_order_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_telegram_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- 5. PAYMENTS TABLE (Demo Payments)
CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL,
    order_id BIGINT NULL REFERENCES orders(id) ON DELETE SET NULL,
    system TEXT NOT NULL DEFAULT 'DEMO_PAY',
    provider TEXT NOT NULL DEFAULT 'DemoPaymentProvider',
    amount BIGINT NULL,
    card_number TEXT DEFAULT '8600 **** **** 1234 (DEMO)',
    comment TEXT DEFAULT 'DEMO_PAYMENT',
    screenshot_file_id TEXT,
    status TEXT DEFAULT 'Approved',
    is_demo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_telegram_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- 6. AUDIT_LOGS TABLE (Sandbox Audit Trail)
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    order_id BIGINT NULL,
    action TEXT NOT NULL,
    details JSONB NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

-- 7. REFERRALS TABLE
CREATE TABLE IF NOT EXISTS referrals (
    id BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL,
    reward INTEGER DEFAULT 80,
    is_demo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);

-- 8. BOT SETTINGS TABLE
CREATE TABLE IF NOT EXISTS bot_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SEED DATA (Demo Simulation)
-- ============================================================

INSERT INTO channels (name, link, username, is_active) VALUES
('siyasi (Demo)', 'https://t.me/siyasi_rasmiy', '@siyasi_rasmiy', TRUE),
('Turfa Seen (Demo)', 'https://t.me/TurfaSeen', '@TurfaSeen', TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO services (platform, category, service_id_external, name, price_per_1000, min_order, max_order, description, estimated_time, is_free, is_demo) VALUES
('Telegram', 'Reaksiya', 200, '🎁 Tekin Reaksiya (50 tagacha)', 0, 1, 50, 'Telegram postlari uchun 50 tagacha mutlaqo bepul reaksiya! Istalgan emojini tanlang.', '1-3 daqiqa', TRUE, TRUE),
('Telegram', 'Obunachi', 340, 'Tekin Obunachi (Demo)', 0, 1, 40, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', TRUE, TRUE),
('Telegram', 'Obunachi', 101, '30 Kun kafolat (Demo)', 8900, 50, 50000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('Telegram', 'Reaksiya', 201, 'Aralash reaksiyalar (👍❤️🔥) (Demo)', 1200, 10, 100000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('Telegram', 'Ko''rishlar', 301, 'Oxirgi 1 ta post ko''rishlar (Demo)', 350, 50, 500000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('Telegram', 'Boost ovoz', 401, 'Kanal uchun Boost (Demo)', 4500, 1, 500, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('Telegram', 'Hikoya', 501, 'Story ko''rishlar (Demo)', 2900, 50, 50000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('Telegram', 'O''zbek tarmoq', 601, 'O''zbek jonli obunachi (Demo)', 28000, 50, 20000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('Instagram', 'Obunachi', 701, 'Instagram Obunachi (Demo)', 7500, 50, 100000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('Instagram', 'Ko''rishlar', 703, 'Instagram Reels ko''rishlar (Demo)', 400, 100, 1000000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('YouTube', 'Obunachi', 801, 'YouTube Obunachi (Demo)', 85000, 50, 10000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('YouTube', 'Ko''rishlar', 802, 'YouTube Video Ko''rishlar (Demo)', 19000, 100, 500000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('TikTok', 'Obunachi', 901, 'TikTok Obunachi (Demo)', 18000, 50, 50000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE),
('TikTok', 'Ko''rishlar', 902, 'TikTok Video Ko''rishlar (Demo)', 250, 100, 1000000, 'DEMO MODE — Faqat test simulyatsiyasi', '1-5 daqiqa (Demo)', FALSE, TRUE)
ON CONFLICT DO NOTHING;

