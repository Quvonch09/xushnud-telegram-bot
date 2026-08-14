-- ============================================================
-- Turfa Seen | Rasmiy - Telegram Bot Database Schema (Supabase)
-- ============================================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    balance BIGINT DEFAULT 0,
    total_deposit BIGINT DEFAULT 0,
    referral_id BIGINT NULL,
    referral_count INTEGER DEFAULT 0,
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_referral_count ON users(referral_count DESC);

-- 2. CHANNELS TABLE (Mandatory Subscription)
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    link TEXT NOT NULL,
    username TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. SERVICES TABLE
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    platform TEXT NOT NULL, -- Telegram, Instagram, YouTube, TikTok
    category TEXT NOT NULL, -- Reaksiya, Ko'rishlar, Obunachi, Boost ovoz, Hikoya, O'zbek tarmoq
    service_id_external INTEGER, -- External provider ID
    name TEXT NOT NULL,
    price_per_1000 BIGINT NOT NULL, -- Price in UZS
    min_order INTEGER NOT NULL DEFAULT 10,
    max_order INTEGER NOT NULL DEFAULT 100000,
    description TEXT DEFAULT 'Faqat ommaviy kanal va guruhlar uchun ishlaydi!',
    is_free BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_services_platform_cat ON services(platform, category);

-- 4. ORDERS TABLE
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL,
    service_id INTEGER REFERENCES services(id) ON DELETE SET NULL,
    service_name TEXT,
    link TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price BIGINT NOT NULL,
    status TEXT DEFAULT 'Pending', -- Pending, InProgress, Completed, Canceled
    external_order_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_telegram_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- 5. PAYMENTS TABLE
CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL,
    system TEXT NOT NULL, -- CLICK, PAYME, UZUM, PAYNET
    amount BIGINT NULL,
    card_number TEXT DEFAULT '5614684605929718',
    comment TEXT DEFAULT '8048583227',
    screenshot_file_id TEXT,
    status TEXT DEFAULT 'Pending', -- Pending, Approved, Rejected
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_telegram_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- 6. REFERRALS TABLE
CREATE TABLE IF NOT EXISTS referrals (
    id BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL,
    reward INTEGER DEFAULT 80,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Seed Channels (4 required channels from screenshots)
INSERT INTO channels (name, link, username, is_active) VALUES
('siyasi', 'https://t.me/siyasi_rasmiy', '@siyasi_rasmiy', TRUE),
('Turfa Seen | Rasmiy', 'https://t.me/TurfaSeen', '@TurfaSeen', TRUE),
('— Sukut saqlang!', 'https://t.me/sukut_saqlang', '@sukut_saqlang', TRUE),
('— Manfaati', 'https://t.me/manfaati_uz', '@manfaati_uz', TRUE)
ON CONFLICT DO NOTHING;

-- Seed Services
-- Telegram Categories
-- Free service: Tekin Obunachi (ID 340, min 1, max 40, price 0)
INSERT INTO services (platform, category, service_id_external, name, price_per_1000, min_order, max_order, description, is_free) VALUES
('Telegram', 'Obunachi', 340, 'Tekin Obunachi', 0, 1, 40, 'Faqat ommaviy kanal va guruhlar uchun ishlaydi! Kuniga 1 marta buyurtma berish mumkin.', TRUE),
('Telegram', 'Obunachi', 101, '30 Kun kafolat', 8900, 50, 50000, 'Faqat ommaviy kanal va guruhlar uchun ishlaydi!', FALSE),
('Telegram', 'Obunachi', 102, '60 Kun kafolat', 13820, 50, 50000, 'Faqat ommaviy kanal va guruhlar uchun ishlaydi! Tezkor qo''shilish.', FALSE),
('Telegram', 'Obunachi', 103, '90 Kun kafolat', 15700, 50, 50000, 'Faqat ommaviy kanal va guruhlar uchun ishlaydi! Sifatli obunachilar.', FALSE),
('Telegram', 'Obunachi', 104, '180 Kun kafolat', 19999, 100, 100000, 'Faqat ommaviy kanal va guruhlar uchun ishlaydi! Yuqori sifat.', FALSE),
('Telegram', 'Obunachi', 105, '365 Kun kafolat', 35879, 100, 100000, 'Faqat ommaviy kanal va guruhlar uchun ishlaydi! 1 yil kafolat.', FALSE),

-- Reaksiya
('Telegram', 'Reaksiya', 201, 'Aralash reaksiyalar (👍❤️🔥)', 1200, 10, 100000, 'Post havolasini yuboring. Tezkor ishga tushish.', FALSE),
('Telegram', 'Reaksiya', 202, 'Ijobiy reaksiyalar (❤️👏🎉)', 1500, 10, 50000, 'Post havolasini yuboring.', FALSE),

-- Ko'rishlar
('Telegram', 'Ko''rishlar', 301, 'Oxirgi 1 ta post ko''rishlar', 350, 50, 500000, 'Post havolasini yuboring.', FALSE),
('Telegram', 'Ko''rishlar', 302, 'Oxirgi 5 ta post ko''rishlar', 1400, 50, 100000, 'Kanal havolasini yuboring.', FALSE),
('Telegram', 'Ko''rishlar', 303, 'Oxirgi 10 ta post ko''rishlar', 2500, 50, 100000, 'Kanal havolasini yuboring.', FALSE),

-- Boost ovoz
('Telegram', 'Boost ovoz', 401, 'Kanal uchun Boost (1 kunlik)', 4500, 1, 500, 'Kanal havolasini yuboring.', FALSE),
('Telegram', 'Boost ovoz', 402, 'Kanal uchun Boost (7 kunlik)', 18000, 1, 500, 'Kanal havolasini yuboring.', FALSE),

-- Hikoya
('Telegram', 'Hikoya', 501, 'Telegram Story ko''rishlar', 2900, 50, 50000, 'Foydalanuvchi yoki kanal story havolasini yuboring.', FALSE),

-- O'zbek tarmoq
('Telegram', 'O''zbek tarmoq', 601, 'O''zbek jonli obunachi', 28000, 50, 20000, 'Faqat ommaviy o''zbek kanallari uchun.', FALSE),
('Telegram', 'O''zbek tarmoq', 602, 'O''zbek post ko''rishlar', 800, 100, 50000, 'O''zbek auditoriyasi ko''rishlari.', FALSE),

-- Instagram Services
('Instagram', 'Obunachi', 701, 'Instagram Kafolatsiz Obunachi', 7500, 50, 100000, 'Profil ochiq (public) bo''lishi shart.', FALSE),
('Instagram', 'Obunachi', 702, 'Instagram 30 Kun Kafolatli Obunachi', 14500, 50, 100000, 'Profil ochiq bo''lishi shart.', FALSE),
('Instagram', 'Ko''rishlar', 703, 'Instagram Reels ko''rishlar', 400, 100, 1000000, 'Reels video havolasi kerak.', FALSE),
('Instagram', 'Reaksiya', 704, 'Instagram Post Layklari', 3500, 50, 50000, 'Post havolasi kerak.', FALSE),

-- YouTube Services
('YouTube', 'Obunachi', 801, 'YouTube Obunachi (Real)', 85000, 50, 10000, 'Kanal havolasini yuboring.', FALSE),
('YouTube', 'Ko''rishlar', 802, 'YouTube Video Ko''rishlar', 19000, 100, 500000, 'Video havolasini yuboring.', FALSE),
('YouTube', 'Reaksiya', 803, 'YouTube Like', 12000, 50, 20000, 'Video havolasini yuboring.', FALSE),

-- TikTok Services
('TikTok', 'Obunachi', 901, 'TikTok Obunachi', 18000, 50, 50000, 'TikTok profil havolasi kerak.', FALSE),
('TikTok', 'Ko''rishlar', 902, 'TikTok Video Ko''rishlar', 250, 100, 1000000, 'Video havolasini yuboring.', FALSE),
('TikTok', 'Reaksiya', 903, 'TikTok Layklar', 6500, 50, 50000, 'Video havolasini yuboring.', FALSE)
ON CONFLICT DO NOTHING;
