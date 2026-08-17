"""
ZERX XIT - Database Layer
=========================
SQLite database initialization, schema, and helpers.
"""
import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# ─── Connection Helper ──────────────────────────────────────────────
@contextmanager
def get_db():
    """Yield a SQLite connection with row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ─── Schema ─────────────────────────────────────────────────────────
SCHEMA_SQL = """
-- Settings table (platform configuration)
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    verification_code TEXT NOT NULL DEFAULT 'ZERX FOR 2027',
    whatsapp_channel TEXT DEFAULT 'https://whatsapp.com/channel/0029Vb7lJZ12ER6kwDPt042K',
    whatsapp_channel_2 TEXT DEFAULT 'https://whatsapp.com/channel/0029VbC1jHJF1YlOgqFACv0K',
    telegram_main TEXT DEFAULT 'https://t.me/zerxgaming',
    telegram_backup TEXT DEFAULT 'https://t.me/zerx_xits_leaks',
    telegram_leaks TEXT DEFAULT 'https://t.me/zerx_xits_leaks',
    admin_whatsapp TEXT DEFAULT 'https://wa.me/2347066889086',
    mediafire_link TEXT DEFAULT 'https://mediafire.com/zerx',
    setup_video TEXT DEFAULT 'https://youtube.com/zerxsetup',
    vip_price TEXT DEFAULT '₦2,000',
    admin_telegram TEXT DEFAULT '@zerxofficial',
    pay1_number TEXT DEFAULT '911438581',
    pay1_bank TEXT DEFAULT 'PALMPAY',
    pay1_name TEXT DEFAULT 'JOSEPH IME NDARAKE',
    pay2_number TEXT DEFAULT '9114380581',
    pay2_bank TEXT DEFAULT 'SMARTCASH',
    pay2_name TEXT DEFAULT 'RUTH',
    share_count INTEGER DEFAULT 5,
    ai_enabled INTEGER DEFAULT 1,
    gemini_model TEXT DEFAULT 'gemini-1.5-flash',
    gemini_temperature REAL DEFAULT 0.7,
    gemini_max_tokens INTEGER DEFAULT 1024,
    vip_enabled INTEGER DEFAULT 1,
    premium_ai_enabled INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table (every device that visits)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,
    zerx_id TEXT UNIQUE NOT NULL,
    brand TEXT,
    model TEXT,
    processor TEXT,
    gpu TEXT,
    ram TEXT,
    android_version TEXT,
    refresh_rate TEXT,
    play_style TEXT,
    verified INTEGER DEFAULT 0,
    joined_channels INTEGER DEFAULT 0,
    share_progress INTEGER DEFAULT 0,
    last_share_at TIMESTAMP,
    vip INTEGER DEFAULT 0,
    vip_expires TIMESTAMP,
    theme TEXT DEFAULT 'dark',
    generation_count INTEGER DEFAULT 0,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Device database (supported phones)
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    processor TEXT,
    gpu TEXT,
    ram TEXT,
    android_version TEXT,
    refresh_rate TEXT,
    performance_score INTEGER DEFAULT 50,
    gaming_score INTEGER DEFAULT 50,
    release_year INTEGER,
    architecture TEXT,
    battery_size TEXT,
    screen_resolution TEXT,
    UNIQUE(brand, model)
);

-- Bans table
CREATE TABLE IF NOT EXISTS bans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    zerx_id TEXT NOT NULL,
    reason TEXT DEFAULT 'Invalid Verification Code',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generations table
CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    brand TEXT,
    model TEXT,
    play_style TEXT,
    general INTEGER,
    red_dot INTEGER,
    scope2x INTEGER,
    scope4x INTEGER,
    sniper INTEGER,
    free_look INTEGER,
    dpi INTEGER,
    ai_optimized INTEGER DEFAULT 0,
    result_json TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VIP activation requests (payment confirmations)
CREATE TABLE IF NOT EXISTS vip_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    zerx_id TEXT NOT NULL,
    payment_reference TEXT,
    sender_name TEXT,
    receipt_mime TEXT,
    receipt_data TEXT,
    reviewed_at TIMESTAMP,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Appeals table
CREATE TABLE IF NOT EXISTS appeals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zerx_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- XIT preferences (toggle states)
CREATE TABLE IF NOT EXISTS xit_prefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,
    xit_boost INTEGER DEFAULT 0,
    touch_optimization INTEGER DEFAULT 0,
    aim_assist_mode INTEGER DEFAULT 0,
    fps_optimization INTEGER DEFAULT 0,
    sensitivity_lock INTEGER DEFAULT 0,
    gaming_mode INTEGER DEFAULT 0,
    low_ping_mode INTEGER DEFAULT 0,
    performance_mode INTEGER DEFAULT 0,
    dark_theme INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity log
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    action TEXT,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin sessions
CREATE TABLE IF NOT EXISTS admin_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
"""

# ─── Seed Data ──────────────────────────────────────────────────────
DEVICE_SEED = [
    # Samsung
    ("Samsung", "Galaxy S24 Ultra", "Snapdragon 8 Gen 3", "Adreno 750", "12GB", "Android 14", "120Hz", 95, 98, 2024, "ARM64", "5000mAh", "3120x1440"),
    ("Samsung", "Galaxy S24+", "Snapdragon 8 Gen 3", "Adreno 750", "12GB", "Android 14", "120Hz", 93, 96, 2024, "ARM64", "4900mAh", "3120x1440"),
    ("Samsung", "Galaxy S24", "Snapdragon 8 Gen 3", "Adreno 750", "8GB", "Android 14", "120Hz", 92, 95, 2024, "ARM64", "4000mAh", "2340x1080"),
    ("Samsung", "Galaxy S23 Ultra", "Snapdragon 8 Gen 2", "Adreno 740", "12GB", "Android 13", "120Hz", 93, 97, 2023, "ARM64", "5000mAh", "3088x1440"),
    ("Samsung", "Galaxy S23", "Snapdragon 8 Gen 2", "Adreno 740", "8GB", "Android 13", "120Hz", 91, 95, 2023, "ARM64", "3900mAh", "2340x1080"),
    ("Samsung", "Galaxy A56", "Exynos 1580", "Mali-G68", "8GB", "Android 15", "120Hz", 78, 82, 2025, "ARM64", "5000mAh", "2340x1080"),
    ("Samsung", "Galaxy A55", "Exynos 1480", "Xclipse 530", "8GB", "Android 14", "120Hz", 75, 80, 2024, "ARM64", "5000mAh", "2340x1080"),
    ("Samsung", "Galaxy A35", "Exynos 1380", "Mali-G68", "6GB", "Android 14", "120Hz", 70, 75, 2024, "ARM64", "5000mAh", "2340x1080"),
    ("Samsung", "Galaxy A25", "Exynos 1280", "Mali-G68", "6GB", "Android 14", "120Hz", 65, 70, 2024, "ARM64", "5000mAh", "2340x1080"),
    ("Samsung", "Galaxy A15", "Helio G99", "Mali-G57", "4GB", "Android 14", "90Hz", 55, 60, 2024, "ARM64", "5000mAh", "2340x1080"),

    # Vivo
    ("Vivo", "V30", "Snapdragon 7 Gen 3", "Adreno 720", "12GB", "Android 14", "120Hz", 82, 85, 2024, "ARM64", "5000mAh", "2800x1260"),
    ("Vivo", "V29", "Snapdragon 778G", "Adreno 642L", "12GB", "Android 13", "120Hz", 78, 82, 2023, "ARM64", "4600mAh", "2800x1260"),
    ("Vivo", "V25", "Dimensity 900", "Mali-G68", "8GB", "Android 12", "90Hz", 70, 74, 2022, "ARM64", "4500mAh", "2404x1080"),
    ("Vivo", "V23e", "Dimensity 810", "Mali-G57", "8GB", "Android 12", "60Hz", 62, 66, 2022, "ARM64", "4050mAh", "2404x1080"),
    ("Vivo", "Y36", "Snapdragon 680", "Adreno 610", "8GB", "Android 13", "90Hz", 58, 62, 2023, "ARM64", "5000mAh", "2408x1080"),
    ("Vivo", "Y28", "Helio G85", "Mali-G52", "8GB", "Android 14", "90Hz", 55, 58, 2024, "ARM64", "6000mAh", "2408x1080"),
    ("Vivo", "Y03", "Helio G85", "Mali-G52", "4GB", "Android 14", "60Hz", 48, 52, 2024, "ARM64", "5000mAh", "1612x720"),

    # Oppo
    ("Oppo", "Reno 11 Pro", "Snapdragon 8+ Gen 1", "Adreno 730", "12GB", "Android 14", "120Hz", 88, 91, 2024, "ARM64", "4700mAh", "2772x1240"),
    ("Oppo", "Reno 11", "Dimensity 7050", "Mali-G68", "8GB", "Android 14", "120Hz", 76, 80, 2024, "ARM64", "5000mAh", "2412x1080"),
    ("Oppo", "A79 5G", "Dimensity 6020", "Mali-G57", "8GB", "Android 13", "90Hz", 60, 64, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Oppo", "A58", "Helio G85", "Mali-G52", "6GB", "Android 13", "90Hz", 55, 58, 2023, "ARM64", "5000mAh", "2400x1080"),

    # Realme
    ("Realme", "GT 6", "Snapdragon 8s Gen 3", "Adreno 735", "12GB", "Android 14", "120Hz", 90, 93, 2024, "ARM64", "5500mAh", "2780x1264"),
    ("Realme", "GT Neo 6", "Snapdragon 8s Gen 3", "Adreno 735", "12GB", "Android 14", "120Hz", 89, 92, 2024, "ARM64", "5500mAh", "2780x1264"),
    ("Realme", "12 Pro+", "Snapdragon 7s Gen 2", "Adreno 710", "8GB", "Android 14", "120Hz", 78, 82, 2024, "ARM64", "5000mAh", "2412x1080"),
    ("Realme", "12+", "Dimensity 7050", "Mali-G68", "8GB", "Android 14", "120Hz", 74, 78, 2024, "ARM64", "5000mAh", "2400x1080"),
    ("Realme", "C67", "Snapdragon 685", "Adreno 610", "8GB", "Android 13", "90Hz", 56, 60, 2023, "ARM64", "5000mAh", "2400x1080"),

    # Xiaomi
    ("Xiaomi", "14 Ultra", "Snapdragon 8 Gen 3", "Adreno 750", "16GB", "Android 14", "120Hz", 96, 99, 2024, "ARM64", "5000mAh", "3200x1440"),
    ("Xiaomi", "14", "Snapdragon 8 Gen 3", "Adreno 750", "12GB", "Android 14", "120Hz", 94, 97, 2024, "ARM64", "4610mAh", "2670x1200"),
    ("Xiaomi", "13T Pro", "Dimensity 9200+", "Immortalis-G715", "12GB", "Android 13", "144Hz", 90, 94, 2023, "ARM64", "5000mAh", "2712x1220"),

    # Redmi
    ("Redmi", "Note 13 Pro+", "Dimensity 7200-Ultra", "Mali-G610", "12GB", "Android 13", "120Hz", 80, 84, 2024, "ARM64", "5000mAh", "2712x1220"),
    ("Redmi", "Note 13 Pro", "Snapdragon 7s Gen 2", "Adreno 710", "8GB", "Android 13", "120Hz", 76, 80, 2024, "ARM64", "5100mAh", "2712x1220"),
    ("Redmi", "Note 13", "Dimensity 6080", "Mali-G57", "6GB", "Android 13", "120Hz", 68, 72, 2024, "ARM64", "5000mAh", "2400x1080"),
    ("Redmi", "13C", "Helio G85", "Mali-G52", "4GB", "Android 13", "90Hz", 52, 55, 2023, "ARM64", "5000mAh", "1650x720"),

    # Tecno
    ("Tecno", "Phantom V2 Fold", "Dimensity 9000+", "Mali-G710", "12GB", "Android 13", "120Hz", 85, 88, 2023, "ARM64", "5000mAh", "2296x2000"),
    ("Tecno", "Camon 30 Premier", "Dimensity 8200", "Mali-G610", "12GB", "Android 14", "144Hz", 82, 86, 2024, "ARM64", "5000mAh", "2800x1260"),
    ("Tecno", "Pova 6 Pro", "Dimensity 6080", "Mali-G57", "8GB", "Android 14", "120Hz", 68, 72, 2024, "ARM64", "6000mAh", "2436x1080"),
    ("Tecno", "Spark 20 Pro+", "Helio G99", "Mali-G57", "8GB", "Android 13", "120Hz", 60, 64, 2024, "ARM64", "5000mAh", "2460x1080"),
    ("Tecno", "Spark Go 2024", "Helio G85", "Mali-G52", "4GB", "Android 13", "90Hz", 50, 54, 2024, "ARM64", "5000mAh", "1612x720"),

    # Infinix
    ("Infinix", "GT 20 Pro", "Dimensity 8200", "Mali-G610", "12GB", "Android 14", "144Hz", 83, 87, 2024, "ARM64", "5000mAh", "2436x1080"),
    ("Infinix", "Note 40 Pro+", "Dimensity 7020", "IMG BXM-8-256", "12GB", "Android 14", "120Hz", 72, 76, 2024, "ARM64", "4600mAh", "2436x1080"),
    ("Infinix", "Hot 40 Pro", "Helio G99", "Mali-G57", "8GB", "Android 13", "90Hz", 58, 62, 2023, "ARM64", "5000mAh", "2460x1080"),
    ("Infinix", "Smart 8", "Helio G36", "PowerVR GE8320", "4GB", "Android 13", "90Hz", 42, 45, 2023, "ARM64", "5000mAh", "1612x720"),

    # Itel
    ("Itel", "S23+", "Unisoc T616", "Mali-G57", "8GB", "Android 13", "90Hz", 48, 52, 2023, "ARM64", "5000mAh", "2408x1080"),
    ("Itel", "P55 5G", "Dimensity 6080", "Mali-G57", "6GB", "Android 13", "90Hz", 55, 58, 2023, "ARM64", "5000mAh", "1612x720"),
    ("Itel", "A70", "Unisoc T603", "Mali-G57", "4GB", "Android 13", "60Hz", 38, 42, 2023, "ARM64", "5000mAh", "1612x720"),

    # Nothing
    ("Nothing", "Phone 2a", "Dimensity 7200 Pro", "Mali-G610", "12GB", "Android 14", "120Hz", 80, 84, 2024, "ARM64", "5000mAh", "2412x1084"),
    ("Nothing", "Phone 2", "Snapdragon 8+ Gen 1", "Adreno 730", "12GB", "Android 13", "120Hz", 88, 91, 2023, "ARM64", "4700mAh", "2412x1080"),
    ("Nothing", "Phone 1", "Snapdragon 778G+", "Adreno 642L", "8GB", "Android 12", "120Hz", 76, 80, 2022, "ARM64", "4500mAh", "2400x1080"),

    # OnePlus
    ("OnePlus", "12", "Snapdragon 8 Gen 3", "Adreno 750", "16GB", "Android 14", "120Hz", 95, 98, 2024, "ARM64", "5400mAh", "3168x1440"),
    ("OnePlus", "12R", "Snapdragon 8 Gen 2", "Adreno 740", "16GB", "Android 14", "120Hz", 90, 93, 2024, "ARM64", "5500mAh", "2780x1264"),
    ("OnePlus", "Nord 4", "Snapdragon 7+ Gen 3", "Adreno 732", "12GB", "Android 14", "120Hz", 84, 87, 2024, "ARM64", "5500mAh", "2772x1240"),
    ("OnePlus", "Nord CE 4", "Snapdragon 7 Gen 3", "Adreno 720", "8GB", "Android 14", "120Hz", 78, 82, 2024, "ARM64", "5500mAh", "2412x1080"),

    # Google
    ("Google", "Pixel 8 Pro", "Tensor G3", "Mali-G715", "12GB", "Android 14", "120Hz", 90, 92, 2023, "ARM64", "5050mAh", "2992x1344"),
    ("Google", "Pixel 8", "Tensor G3", "Mali-G715", "8GB", "Android 14", "120Hz", 88, 90, 2023, "ARM64", "4575mAh", "2400x1080"),
    ("Google", "Pixel 7a", "Tensor G2", "Mali-G710", "8GB", "Android 13", "90Hz", 78, 81, 2023, "ARM64", "4385mAh", "2400x1080"),

    # Motorola
    ("Motorola", "Edge 50 Ultra", "Snapdragon 8s Gen 3", "Adreno 735", "12GB", "Android 14", "144Hz", 89, 92, 2024, "ARM64", "4500mAh", "2712x1220"),
    ("Motorola", "Edge 50 Pro", "Snapdragon 7 Gen 3", "Adreno 720", "12GB", "Android 14", "144Hz", 82, 85, 2024, "ARM64", "4500mAh", "2712x1220"),
    ("Motorola", "Moto G84", "Snapdragon 695", "Adreno 619", "12GB", "Android 13", "120Hz", 65, 69, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Motorola", "Moto G24", "Helio G85", "Mali-G52", "4GB", "Android 14", "90Hz", 50, 54, 2024, "ARM64", "5000mAh", "1612x720"),

    # Huawei
    ("Huawei", "Mate 60 Pro", "Kirin 9000S", "Maleoon 910", "12GB", "HarmonyOS 4", "120Hz", 88, 90, 2023, "ARM64", "5000mAh", "2720x1260"),
    ("Huawei", "Pura 70 Ultra", "Kirin 9010", "Maleoon 910", "16GB", "HarmonyOS 4", "120Hz", 90, 92, 2024, "ARM64", "5200mAh", "2844x1260"),
    ("Huawei", "nova 12 Pro", "Kirin 8000", "Mali-G610", "12GB", "HarmonyOS 4", "120Hz", 76, 80, 2024, "ARM64", "4600mAh", "2776x1224"),

    # Honor
    ("Honor", "Magic 6 Pro", "Snapdragon 8 Gen 3", "Adreno 750", "12GB", "Android 14", "120Hz", 93, 96, 2024, "ARM64", "5600mAh", "2800x1280"),
    ("Honor", "Magic 6", "Snapdragon 8 Gen 3", "Adreno 750", "12GB", "Android 14", "120Hz", 91, 94, 2024, "ARM64", "5450mAh", "2800x1280"),
    ("Honor", "200 Pro", "Snapdragon 8s Gen 3", "Adreno 735", "12GB", "Android 14", "120Hz", 85, 88, 2024, "ARM64", "5200mAh", "2700x1224"),
    ("Honor", "X9b", "Snapdragon 6 Gen 1", "Adreno 710", "8GB", "Android 13", "120Hz", 62, 66, 2023, "ARM64", "5800mAh", "2652x1200"),

    # Sony
    ("Sony", "Xperia 1 VI", "Snapdragon 8 Gen 3", "Adreno 750", "12GB", "Android 14", "120Hz", 91, 93, 2024, "ARM64", "5000mAh", "2340x1080"),
    ("Sony", "Xperia 5 V", "Snapdragon 8 Gen 2", "Adreno 740", "8GB", "Android 13", "120Hz", 86, 89, 2023, "ARM64", "5000mAh", "2520x1080"),
    ("Sony", "Xperia 10 VI", "Snapdragon 6 Gen 1", "Adreno 710", "8GB", "Android 14", "120Hz", 65, 68, 2024, "ARM64", "5000mAh", "2520x1080"),

    # Nokia
    ("Nokia", "G42 5G", "Snapdragon 480+", "Adreno 619", "6GB", "Android 13", "90Hz", 55, 58, 2023, "ARM64", "5000mAh", "1612x720"),
    ("Nokia", "G22", "Unisoc T606", "Mali-G57", "4GB", "Android 12", "90Hz", 45, 48, 2023, "ARM64", "5050mAh", "1612x720"),
    ("Nokia", "C32", "Unisoc SC9863A", "PowerVR GE8322", "4GB", "Android 13", "60Hz", 35, 38, 2023, "ARM64", "5000mAh", "1600x720"),

    # Apple
    ("Apple", "iPhone 15 Pro Max", "A17 Pro", "Apple GPU 6-core", "8GB", "iOS 17", "120Hz", 96, 98, 2023, "ARM64", "4441mAh", "2796x1290"),
    ("Apple", "iPhone 15 Pro", "A17 Pro", "Apple GPU 6-core", "8GB", "iOS 17", "120Hz", 95, 97, 2023, "ARM64", "3274mAh", "2556x1179"),
    ("Apple", "iPhone 15", "A16 Bionic", "Apple GPU 5-core", "6GB", "iOS 17", "60Hz", 90, 93, 2023, "ARM64", "3349mAh", "2556x1179"),
    ("Apple", "iPhone 14 Pro Max", "A16 Bionic", "Apple GPU 5-core", "6GB", "iOS 16", "120Hz", 93, 96, 2022, "ARM64", "4323mAh", "2796x1290"),
    ("Apple", "iPhone 14", "A15 Bionic", "Apple GPU 5-core", "6GB", "iOS 16", "60Hz", 88, 91, 2022, "ARM64", "3279mAh", "2532x1170"),
    ("Apple", "iPhone 13", "A15 Bionic", "Apple GPU 4-core", "4GB", "iOS 15", "60Hz", 85, 88, 2021, "ARM64", "3227mAh", "2532x1170"),
    ("Apple", "iPhone SE 2022", "A15 Bionic", "Apple GPU 4-core", "4GB", "iOS 15", "60Hz", 78, 81, 2022, "ARM64", "2018mAh", "1334x750"),
]

# Extended catalogue — mid-range and budget models common in Africa & Asia.
DEVICE_SEED += [
    # Samsung (extended)
    ("Samsung", "Galaxy S25 Ultra", "Snapdragon 8 Elite", "Adreno 830", "12GB", "Android 15", "120Hz", 98, 99, 2025, "ARM64", "5000mAh", "3120x1440"),
    ("Samsung", "Galaxy S22 Ultra", "Snapdragon 8 Gen 1", "Adreno 730", "12GB", "Android 12", "120Hz", 89, 92, 2022, "ARM64", "5000mAh", "3088x1440"),
    ("Samsung", "Galaxy S21 FE", "Snapdragon 888", "Adreno 660", "8GB", "Android 12", "120Hz", 85, 88, 2022, "ARM64", "4500mAh", "2340x1080"),
    ("Samsung", "Galaxy A54", "Exynos 1380", "Mali-G68", "8GB", "Android 13", "120Hz", 72, 76, 2023, "ARM64", "5000mAh", "2340x1080"),
    ("Samsung", "Galaxy A53", "Exynos 1280", "Mali-G68", "6GB", "Android 12", "120Hz", 68, 72, 2022, "ARM64", "5000mAh", "2400x1080"),
    ("Samsung", "Galaxy A34", "Dimensity 1080", "Mali-G68", "6GB", "Android 13", "120Hz", 69, 73, 2023, "ARM64", "5000mAh", "2340x1080"),
    ("Samsung", "Galaxy A33", "Exynos 1280", "Mali-G68", "6GB", "Android 12", "90Hz", 64, 68, 2022, "ARM64", "5000mAh", "2400x1080"),
    ("Samsung", "Galaxy A24", "Helio G99", "Mali-G57", "6GB", "Android 13", "90Hz", 58, 62, 2023, "ARM64", "5000mAh", "2340x1080"),
    ("Samsung", "Galaxy A23", "Snapdragon 680", "Adreno 610", "4GB", "Android 12", "120Hz", 56, 60, 2022, "ARM64", "5000mAh", "2408x1080"),
    ("Samsung", "Galaxy A14", "Helio G80", "Mali-G52", "4GB", "Android 13", "90Hz", 50, 54, 2023, "ARM64", "5000mAh", "2408x1080"),
    ("Samsung", "Galaxy A13", "Exynos 850", "Mali-G52", "4GB", "Android 12", "60Hz", 44, 48, 2022, "ARM64", "5000mAh", "2408x1080"),
    ("Samsung", "Galaxy A05s", "Snapdragon 680", "Adreno 610", "4GB", "Android 13", "90Hz", 52, 56, 2023, "ARM64", "5000mAh", "2408x1080"),
    ("Samsung", "Galaxy A04", "Helio P35", "PowerVR GE8320", "4GB", "Android 12", "60Hz", 36, 40, 2022, "ARM64", "5000mAh", "1560x720"),
    ("Samsung", "Galaxy M34", "Exynos 1280", "Mali-G68", "6GB", "Android 13", "120Hz", 65, 69, 2023, "ARM64", "6000mAh", "2340x1080"),
    ("Samsung", "Galaxy M14", "Exynos 1330", "Mali-G68", "4GB", "Android 13", "90Hz", 56, 60, 2023, "ARM64", "6000mAh", "2408x1080"),

    # Xiaomi / Redmi / POCO (extended)
    ("Xiaomi", "13 Pro", "Snapdragon 8 Gen 2", "Adreno 740", "12GB", "Android 13", "120Hz", 93, 96, 2023, "ARM64", "4820mAh", "3200x1440"),
    ("Xiaomi", "12 Lite", "Snapdragon 778G", "Adreno 642L", "8GB", "Android 12", "120Hz", 74, 78, 2022, "ARM64", "4300mAh", "2400x1080"),
    ("Xiaomi", "Redmi Note 14 Pro", "Dimensity 7300 Ultra", "Mali-G615", "8GB", "Android 14", "120Hz", 78, 82, 2025, "ARM64", "5500mAh", "2712x1220"),
    ("Redmi", "Note 12 Pro", "Dimensity 1080", "Mali-G68", "8GB", "Android 12", "120Hz", 72, 76, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Redmi", "Note 12", "Snapdragon 685", "Adreno 610", "6GB", "Android 13", "120Hz", 60, 64, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Redmi", "Note 11", "Snapdragon 680", "Adreno 610", "6GB", "Android 11", "90Hz", 57, 61, 2022, "ARM64", "5000mAh", "2400x1080"),
    ("Redmi", "Note 10", "Snapdragon 678", "Adreno 612", "4GB", "Android 11", "60Hz", 55, 59, 2021, "ARM64", "5000mAh", "2400x1080"),
    ("Redmi", "Note 9", "Helio G85", "Mali-G52", "4GB", "Android 10", "60Hz", 50, 54, 2020, "ARM64", "5020mAh", "2340x1080"),
    ("Redmi", "12", "Helio G88", "Mali-G52", "8GB", "Android 13", "90Hz", 55, 58, 2023, "ARM64", "5000mAh", "2460x1080"),
    ("Redmi", "A3", "Helio G36", "PowerVR GE8320", "4GB", "Android 14", "90Hz", 40, 43, 2024, "ARM64", "5000mAh", "1640x720"),
    ("POCO", "F6", "Snapdragon 8s Gen 3", "Adreno 735", "12GB", "Android 14", "120Hz", 90, 93, 2024, "ARM64", "5000mAh", "2712x1220"),
    ("POCO", "X6 Pro", "Dimensity 8300 Ultra", "Mali-G615", "12GB", "Android 14", "120Hz", 87, 90, 2024, "ARM64", "5000mAh", "2712x1220"),
    ("POCO", "X5 Pro", "Snapdragon 778G", "Adreno 642L", "8GB", "Android 12", "120Hz", 76, 80, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("POCO", "M6 Pro", "Helio G99 Ultra", "Mali-G57", "8GB", "Android 13", "120Hz", 63, 67, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("POCO", "C65", "Helio G85", "Mali-G52", "6GB", "Android 13", "90Hz", 52, 56, 2023, "ARM64", "5000mAh", "1650x720"),

    # Tecno (extended)
    ("Tecno", "Camon 20 Pro", "Helio G99", "Mali-G57", "8GB", "Android 13", "120Hz", 62, 66, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Tecno", "Camon 19", "Helio G85", "Mali-G52", "6GB", "Android 12", "60Hz", 54, 58, 2022, "ARM64", "5000mAh", "2460x1080"),
    ("Tecno", "Camon 30", "Helio G99 Ultimate", "Mali-G57", "8GB", "Android 14", "120Hz", 65, 69, 2024, "ARM64", "5000mAh", "2436x1080"),
    ("Tecno", "Spark 20", "Helio G85", "Mali-G52", "8GB", "Android 13", "90Hz", 53, 57, 2024, "ARM64", "5000mAh", "1612x720"),
    ("Tecno", "Spark 20 Pro", "Helio G99", "Mali-G57", "8GB", "Android 13", "120Hz", 60, 64, 2024, "ARM64", "5000mAh", "2400x1080"),
    ("Tecno", "Spark 10 Pro", "Helio G88", "Mali-G52", "8GB", "Android 13", "90Hz", 55, 59, 2023, "ARM64", "5000mAh", "2460x1080"),
    ("Tecno", "Spark 10", "Helio G37", "PowerVR GE8320", "4GB", "Android 13", "90Hz", 43, 47, 2023, "ARM64", "5000mAh", "1612x720"),
    ("Tecno", "Spark 9", "Helio G37", "PowerVR GE8320", "4GB", "Android 12", "90Hz", 42, 46, 2022, "ARM64", "5000mAh", "1612x720"),
    ("Tecno", "Pova 5", "Helio G99", "Mali-G57", "8GB", "Android 13", "120Hz", 61, 65, 2023, "ARM64", "6000mAh", "2460x1080"),
    ("Tecno", "Pova 5 Pro", "Dimensity 6080", "Mali-G57", "8GB", "Android 13", "120Hz", 66, 70, 2023, "ARM64", "5000mAh", "2436x1080"),
    ("Tecno", "Pova 6 Neo", "Helio G99 Ultimate", "Mali-G57", "8GB", "Android 14", "120Hz", 62, 66, 2024, "ARM64", "7000mAh", "2436x1080"),
    ("Tecno", "Pop 8", "Unisoc T606", "Mali-G57", "3GB", "Android 13", "90Hz", 38, 42, 2024, "ARM64", "5000mAh", "1612x720"),
    ("Tecno", "Camon 40 Pro", "Dimensity 7300 Ultra", "Mali-G615", "8GB", "Android 15", "144Hz", 78, 82, 2025, "ARM64", "5200mAh", "2436x1080"),

    # Infinix (extended)
    ("Infinix", "Note 40", "Helio G99 Ultimate", "Mali-G57", "8GB", "Android 14", "120Hz", 63, 67, 2024, "ARM64", "5000mAh", "2436x1080"),
    ("Infinix", "Note 40 Pro", "Dimensity 7020", "IMG BXM-8-256", "12GB", "Android 14", "120Hz", 71, 75, 2024, "ARM64", "5000mAh", "2436x1080"),
    ("Infinix", "Note 30", "Helio G99", "Mali-G57", "8GB", "Android 13", "120Hz", 61, 65, 2023, "ARM64", "5000mAh", "2460x1080"),
    ("Infinix", "Note 30 VIP", "Dimensity 8050", "Mali-G77", "12GB", "Android 13", "120Hz", 80, 84, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Infinix", "Note 12", "Helio G88", "Mali-G52", "6GB", "Android 12", "60Hz", 54, 58, 2022, "ARM64", "5000mAh", "2400x1080"),
    ("Infinix", "Hot 40", "Helio G88", "Mali-G52", "8GB", "Android 13", "90Hz", 55, 59, 2023, "ARM64", "5000mAh", "2460x1080"),
    ("Infinix", "Hot 40i", "Unisoc T606", "Mali-G57", "8GB", "Android 13", "90Hz", 45, 49, 2023, "ARM64", "5000mAh", "1612x720"),
    ("Infinix", "Hot 30", "Helio G88", "Mali-G52", "8GB", "Android 12", "90Hz", 54, 58, 2023, "ARM64", "5000mAh", "2460x1080"),
    ("Infinix", "Hot 30i", "Helio G37", "PowerVR GE8320", "4GB", "Android 12", "90Hz", 43, 47, 2023, "ARM64", "5000mAh", "1612x720"),
    ("Infinix", "Hot 50 Pro", "Helio G100", "Mali-G57", "8GB", "Android 14", "120Hz", 64, 68, 2024, "ARM64", "5000mAh", "2436x1080"),
    ("Infinix", "Zero 30", "Dimensity 8020", "Mali-G77", "12GB", "Android 13", "144Hz", 79, 83, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Infinix", "Smart 9", "Unisoc T615", "Mali-G57", "4GB", "Android 14", "90Hz", 44, 48, 2024, "ARM64", "5000mAh", "1612x720"),
    ("Infinix", "GT 10 Pro", "Dimensity 8050", "Mali-G77", "8GB", "Android 13", "120Hz", 80, 84, 2023, "ARM64", "5000mAh", "2400x1080"),

    # itel (extended)
    ("Itel", "S24", "Helio G91", "Mali-G52", "8GB", "Android 13", "90Hz", 50, 54, 2024, "ARM64", "5000mAh", "2400x1080"),
    ("Itel", "P55", "Unisoc T606", "Mali-G57", "8GB", "Android 13", "90Hz", 46, 50, 2023, "ARM64", "5000mAh", "1612x720"),
    ("Itel", "A80", "Unisoc T7100", "Mali-G57", "4GB", "Android 14", "90Hz", 42, 46, 2024, "ARM64", "5000mAh", "1612x720"),
    ("Itel", "A60s", "Unisoc SC9863A", "PowerVR GE8322", "4GB", "Android 12", "60Hz", 32, 36, 2023, "ARM64", "4000mAh", "1600x720"),

    # Oppo / Realme / OnePlus (extended)
    ("Oppo", "Reno 12", "Dimensity 7300 Energy", "Mali-G615", "12GB", "Android 14", "120Hz", 79, 83, 2024, "ARM64", "5000mAh", "2412x1080"),
    ("Oppo", "Reno 10", "Dimensity 7050", "Mali-G68", "8GB", "Android 13", "120Hz", 74, 78, 2023, "ARM64", "5000mAh", "2412x1080"),
    ("Oppo", "Reno 8T", "Snapdragon 680", "Adreno 610", "8GB", "Android 13", "90Hz", 58, 62, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Oppo", "A98", "Snapdragon 695", "Adreno 619", "8GB", "Android 13", "120Hz", 64, 68, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Oppo", "A78", "Snapdragon 680", "Adreno 610", "8GB", "Android 13", "90Hz", 57, 61, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Oppo", "A18", "Helio G85", "Mali-G52", "4GB", "Android 13", "90Hz", 51, 55, 2023, "ARM64", "5000mAh", "1612x720"),
    ("Realme", "13 Pro+", "Snapdragon 7s Gen 2", "Adreno 710", "12GB", "Android 14", "120Hz", 80, 84, 2024, "ARM64", "5200mAh", "2412x1080"),
    ("Realme", "11 Pro", "Dimensity 7050", "Mali-G68", "8GB", "Android 13", "120Hz", 74, 78, 2023, "ARM64", "5000mAh", "2412x1080"),
    ("Realme", "10", "Helio G99", "Mali-G57", "8GB", "Android 13", "90Hz", 62, 66, 2022, "ARM64", "5000mAh", "2400x1080"),
    ("Realme", "C55", "Helio G88", "Mali-G52", "6GB", "Android 13", "90Hz", 55, 59, 2023, "ARM64", "5000mAh", "2412x1080"),
    ("Realme", "C53", "Unisoc T612", "Mali-G57", "6GB", "Android 13", "90Hz", 48, 52, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Realme", "Narzo 70", "Dimensity 7050", "Mali-G68", "8GB", "Android 14", "120Hz", 73, 77, 2024, "ARM64", "5000mAh", "2400x1080"),
    ("OnePlus", "11", "Snapdragon 8 Gen 2", "Adreno 740", "12GB", "Android 13", "120Hz", 93, 96, 2023, "ARM64", "5000mAh", "3216x1440"),
    ("OnePlus", "Nord 3", "Dimensity 9000", "Mali-G710", "8GB", "Android 13", "120Hz", 86, 89, 2023, "ARM64", "5000mAh", "2772x1240"),
    ("OnePlus", "Nord CE 3 Lite", "Snapdragon 695", "Adreno 619", "8GB", "Android 13", "120Hz", 64, 68, 2023, "ARM64", "5000mAh", "2400x1080"),

    # Vivo (extended)
    ("Vivo", "X100", "Dimensity 9300", "Immortalis-G720", "12GB", "Android 14", "120Hz", 95, 97, 2024, "ARM64", "5000mAh", "2800x1260"),
    ("Vivo", "V40", "Snapdragon 7 Gen 3", "Adreno 720", "8GB", "Android 14", "120Hz", 81, 85, 2024, "ARM64", "5500mAh", "2800x1260"),
    ("Vivo", "Y100", "Snapdragon 695", "Adreno 619", "8GB", "Android 13", "120Hz", 65, 69, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Vivo", "Y27", "Helio G85", "Mali-G52", "6GB", "Android 13", "90Hz", 54, 58, 2023, "ARM64", "5000mAh", "2388x1080"),
    ("Vivo", "Y17s", "Helio G85", "Mali-G52", "4GB", "Android 13", "60Hz", 50, 54, 2023, "ARM64", "5000mAh", "1612x720"),

    # Google / Motorola / Nokia / Honor / Huawei (extended)
    ("Google", "Pixel 9 Pro", "Tensor G4", "Mali-G715", "16GB", "Android 15", "120Hz", 92, 94, 2024, "ARM64", "4700mAh", "2856x1280"),
    ("Google", "Pixel 6a", "Tensor", "Mali-G78", "6GB", "Android 12", "60Hz", 76, 79, 2022, "ARM64", "4410mAh", "2400x1080"),
    ("Motorola", "Moto G64", "Dimensity 7025", "Mali-G615", "8GB", "Android 14", "120Hz", 68, 72, 2024, "ARM64", "6000mAh", "2400x1080"),
    ("Motorola", "Moto G54", "Dimensity 7020", "Mali-G57", "8GB", "Android 13", "120Hz", 66, 70, 2023, "ARM64", "6000mAh", "2400x1080"),
    ("Motorola", "Moto G14", "Unisoc T616", "Mali-G57", "4GB", "Android 13", "60Hz", 47, 51, 2023, "ARM64", "5000mAh", "2400x1080"),
    ("Nokia", "X30", "Snapdragon 695", "Adreno 619", "8GB", "Android 12", "90Hz", 63, 67, 2022, "ARM64", "4200mAh", "2400x1080"),
    ("Nokia", "G60", "Snapdragon 695", "Adreno 619", "6GB", "Android 12", "120Hz", 62, 66, 2022, "ARM64", "4500mAh", "2400x1080"),
    ("Honor", "X8b", "Snapdragon 680", "Adreno 610", "8GB", "Android 13", "90Hz", 57, 61, 2024, "ARM64", "4500mAh", "2412x1080"),
    ("Honor", "90", "Snapdragon 7 Gen 1", "Adreno 644", "8GB", "Android 13", "120Hz", 77, 81, 2023, "ARM64", "5000mAh", "2664x1200"),
    ("Huawei", "nova 11", "Snapdragon 778G", "Adreno 642L", "8GB", "HarmonyOS 3", "120Hz", 74, 78, 2023, "ARM64", "4500mAh", "2412x1084"),
    ("Huawei", "nova Y72", "Snapdragon 680", "Adreno 610", "8GB", "HarmonyOS 3", "90Hz", 56, 60, 2024, "ARM64", "6000mAh", "2388x1080"),

    # Apple (extended)
    ("Apple", "iPhone 16 Pro Max", "A18 Pro", "Apple GPU 6-core", "8GB", "iOS 18", "120Hz", 99, 100, 2024, "ARM64", "4685mAh", "2868x1320"),
    ("Apple", "iPhone 16", "A18", "Apple GPU 5-core", "8GB", "iOS 18", "60Hz", 94, 96, 2024, "ARM64", "3561mAh", "2556x1179"),
    ("Apple", "iPhone 13 Pro Max", "A15 Bionic", "Apple GPU 5-core", "6GB", "iOS 15", "120Hz", 90, 93, 2021, "ARM64", "4352mAh", "2778x1284"),
    ("Apple", "iPhone 12", "A14 Bionic", "Apple GPU 4-core", "4GB", "iOS 14", "60Hz", 82, 85, 2020, "ARM64", "2815mAh", "2532x1170"),
    ("Apple", "iPhone 11", "A13 Bionic", "Apple GPU 4-core", "4GB", "iOS 13", "60Hz", 78, 81, 2019, "ARM64", "3110mAh", "1792x828"),
]

def _ensure_columns(conn, table, columns):
    """Add any missing columns to an existing table (lightweight migration)."""
    existing = {r['name'] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, decl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")

def init_db():
    """Initialize database with schema and seed data."""
    with get_db() as conn:
        # Create tables
        conn.executescript(SCHEMA_SQL)

        # Migrate older databases
        _ensure_columns(conn, 'settings', {
            'whatsapp_channel_2': "TEXT DEFAULT 'https://whatsapp.com/channel/0029VbC1jHJF1YlOgqFACv0K'",
            'telegram_leaks': "TEXT DEFAULT 'https://t.me/zerx_xits_leaks'",
            'admin_whatsapp': "TEXT DEFAULT 'https://wa.me/2347066889086'",
            'pay1_number': "TEXT DEFAULT '911438581'",
            'pay1_bank': "TEXT DEFAULT 'PALMPAY'",
            'pay1_name': "TEXT DEFAULT 'JOSEPH IME NDARAKE'",
            'pay2_number': "TEXT DEFAULT '9114380581'",
            'pay2_bank': "TEXT DEFAULT 'SMARTCASH'",
            'pay2_name': "TEXT DEFAULT 'RUTH'",
        })
        _ensure_columns(conn, 'generations', {'result_json': 'TEXT'})
        _ensure_columns(conn, 'users', {
            'joined_channels': 'INTEGER DEFAULT 0',
            'share_progress': 'INTEGER DEFAULT 0',
            'last_share_at': 'TIMESTAMP',
        })
        _ensure_columns(conn, 'vip_requests', {
            'receipt_mime': 'TEXT',
            'receipt_data': 'TEXT',
            'reviewed_at': 'TIMESTAMP',
        })
        conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_brand ON devices(brand)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_generations_device ON generations(device_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_requests_status ON vip_requests(status)")

        # Seed settings if empty
        cur = conn.execute("SELECT 1 FROM settings LIMIT 1")
        if not cur.fetchone():
            conn.execute("""
                INSERT INTO settings (id, verification_code, whatsapp_channel, whatsapp_channel_2,
                telegram_main, telegram_backup, telegram_leaks, admin_whatsapp,
                mediafire_link, setup_video, vip_price, admin_telegram,
                share_count, ai_enabled, gemini_model, gemini_temperature, gemini_max_tokens,
                vip_enabled, premium_ai_enabled)
                VALUES (1, 'ZERX FOR 2027',
                'https://whatsapp.com/channel/0029Vb7lJZ12ER6kwDPt042K',
                'https://whatsapp.com/channel/0029VbC1jHJF1YlOgqFACv0K',
                'https://t.me/zerxgaming', 'https://t.me/zerx_xits_leaks',
                'https://t.me/zerx_xits_leaks', 'https://wa.me/2347066889086',
                'https://mediafire.com/zerx', 'https://youtube.com/zerxsetup',
                '₦2,000', '@zerxofficial', 5, 1, 'gemini-1.5-flash', 0.7, 1024, 1, 1)
            """)

        # Seed devices (idempotent — new models added on every boot)
        conn.executemany("""
            INSERT OR IGNORE INTO devices
            (brand, model, processor, gpu, ram, android_version, refresh_rate,
            performance_score, gaming_score, release_year, architecture, battery_size, screen_resolution)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, DEVICE_SEED)

# ─── Helper Queries ─────────────────────────────────────────────────
def get_settings():
    with get_db() as conn:
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        return dict(row) if row else {}

def update_settings(**kwargs):
    with get_db() as conn:
        allowed = ['verification_code', 'whatsapp_channel', 'whatsapp_channel_2',
                   'telegram_main', 'telegram_backup', 'telegram_leaks', 'admin_whatsapp',
                   'mediafire_link', 'setup_video', 'vip_price',
                   'admin_telegram', 'share_count', 'ai_enabled', 'gemini_model',
                   'gemini_temperature', 'gemini_max_tokens', 'vip_enabled', 'premium_ai_enabled',
                   'pay1_number', 'pay1_bank', 'pay1_name',
                   'pay2_number', 'pay2_bank', 'pay2_name']
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                vals.append(v)
        if sets:
            vals.append(1)
            conn.execute(f"UPDATE settings SET {', '.join(sets)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", vals)

def get_device_by_brand_model(brand, model):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM devices WHERE brand = ? AND model = ?", (brand, model)
        ).fetchone()
        return dict(row) if row else None

def get_models_by_brand(brand):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT model FROM devices WHERE brand = ? ORDER BY model", (brand,)
        ).fetchall()
        return [r['model'] for r in rows]

def get_all_brands():
    with get_db() as conn:
        rows = conn.execute("SELECT DISTINCT brand FROM devices ORDER BY brand").fetchall()
        return [r['brand'] for r in rows]

def get_or_create_user(device_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE device_id = ?", (device_id,)).fetchone()
        if row:
            conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE device_id = ?", (device_id,))
            return dict(row)
        # Create new user
        import secrets
        zerx_id = f"ZX-{secrets.token_hex(4).upper()}"
        conn.execute("""
            INSERT INTO users (device_id, zerx_id) VALUES (?, ?)
        """, (device_id, zerx_id))
        # Create xit_prefs
        conn.execute("INSERT OR IGNORE INTO xit_prefs (device_id) VALUES (?)", (device_id,))
        row = conn.execute("SELECT * FROM users WHERE device_id = ?", (device_id,)).fetchone()
        return dict(row)

def is_banned(device_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM bans WHERE device_id = ? AND status = 'active'", (device_id,)
        ).fetchone()
        return dict(row) if row else None

def ban_device(device_id, zerx_id, reason="Invalid Verification Code"):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO bans (device_id, zerx_id, reason, status)
            VALUES (?, ?, ?, 'active')
        """, (device_id, zerx_id, reason))

def unban_device(device_id):
    with get_db() as conn:
        conn.execute("UPDATE bans SET status = 'removed' WHERE device_id = ?", (device_id,))

def log_activity(device_id, action, details="", ip=""):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO activity_log (device_id, action, details, ip_address)
            VALUES (?, ?, ?, ?)
        """, (device_id, action, details, ip))

def get_user_xit_prefs(device_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM xit_prefs WHERE device_id = ?", (device_id,)).fetchone()
        if not row:
            conn.execute("INSERT INTO xit_prefs (device_id) VALUES (?)", (device_id,))
            row = conn.execute("SELECT * FROM xit_prefs WHERE device_id = ?", (device_id,)).fetchone()
        return dict(row)

def update_xit_prefs(device_id, **kwargs):
    with get_db() as conn:
        allowed = ['xit_boost', 'touch_optimization', 'aim_assist_mode', 'fps_optimization',
                   'sensitivity_lock', 'gaming_mode', 'low_ping_mode', 'performance_mode', 'dark_theme']
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                vals.append(1 if v else 0)
        if sets:
            vals.append(device_id)
            conn.execute(f"UPDATE xit_prefs SET {', '.join(sets)}, updated_at = CURRENT_TIMESTAMP WHERE device_id = ?", vals)

def save_generation(device_id, brand, model, play_style, values):
    with get_db() as conn:
        cur = conn.execute("""
            INSERT INTO generations 
            (device_id, brand, model, play_style, general, red_dot, scope2x, scope4x, sniper, free_look, dpi, ai_optimized, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (device_id, brand, model, play_style, 
              values.get('general', 50), values.get('red_dot', 50),
              values.get('scope2x', 50), values.get('scope4x', 50),
              values.get('sniper', 50), values.get('free_look', 50),
              values.get('dpi', 400), values.get('ai_optimized', 0),
              json.dumps(values)))
        conn.execute("UPDATE users SET generation_count = generation_count + 1 WHERE device_id = ?", (device_id,))
        return cur.lastrowid

def get_latest_generation(device_id):
    with get_db() as conn:
        row = conn.execute("""
            SELECT * FROM generations WHERE device_id = ?
            ORDER BY id DESC LIMIT 1
        """, (device_id,)).fetchone()
        return dict(row) if row else None

def search_devices(query, limit=20):
    q = f"%{query}%"
    with get_db() as conn:
        rows = conn.execute("""
            SELECT brand, model FROM devices
            WHERE brand || ' ' || model LIKE ? OR model LIKE ? OR brand LIKE ?
            ORDER BY brand, model LIMIT ?
        """, (q, q, q, limit)).fetchall()
        return [dict(r) for r in rows]

# ─── VIP Requests ───────────────────────────────────────────────
def create_vip_request(device_id, zerx_id, payment_reference='', sender_name='',
                       receipt_mime=None, receipt_data=None):
    """Create a pending VIP request, or attach a newer receipt to the existing one."""
    with get_db() as conn:
        existing = conn.execute("""
            SELECT id FROM vip_requests WHERE device_id = ? AND status = 'pending'
        """, (device_id,)).fetchone()
        if existing:
            conn.execute("""
                UPDATE vip_requests SET payment_reference = ?, sender_name = ?,
                receipt_mime = COALESCE(?, receipt_mime), receipt_data = COALESCE(?, receipt_data)
                WHERE id = ?
            """, (payment_reference, sender_name, receipt_mime, receipt_data, existing['id']))
            return existing['id'], False
        cur = conn.execute("""
            INSERT INTO vip_requests
            (device_id, zerx_id, payment_reference, sender_name, receipt_mime, receipt_data, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (device_id, zerx_id, payment_reference, sender_name, receipt_mime, receipt_data))
        return cur.lastrowid, True

def get_vip_request(request_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM vip_requests WHERE id = ?", (request_id,)).fetchone()
        return dict(row) if row else None

def set_user_vip(device_id, vip):
    with get_db() as conn:
        conn.execute("UPDATE users SET vip = ? WHERE device_id = ?", (1 if vip else 0, device_id))

def get_vip_request_status(device_id):
    with get_db() as conn:
        row = conn.execute("""
            SELECT id, device_id, zerx_id, payment_reference, sender_name, status,
                   created_at, reviewed_at
            FROM vip_requests WHERE device_id = ?
            ORDER BY id DESC LIMIT 1
        """, (device_id,)).fetchone()
        return dict(row) if row else None

def get_vip_requests(status='pending'):
    """List VIP requests without the (large) receipt payload."""
    columns = """id, device_id, zerx_id, payment_reference, sender_name, status,
                 created_at, reviewed_at,
                 CASE WHEN receipt_data IS NOT NULL AND receipt_data != '' THEN 1 ELSE 0 END AS has_receipt"""
    with get_db() as conn:
        if status:
            rows = conn.execute(
                f"SELECT {columns} FROM vip_requests WHERE status = ? ORDER BY created_at DESC",
                (status,)).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {columns} FROM vip_requests ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

def set_vip_request_status(request_id, status):
    with get_db() as conn:
        req = conn.execute("SELECT * FROM vip_requests WHERE id = ?", (request_id,)).fetchone()
        if not req:
            return None
        conn.execute(
            "UPDATE vip_requests SET status = ?, reviewed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, request_id))
        conn.execute("UPDATE users SET vip = ? WHERE device_id = ?",
                     (1 if status == 'approved' else 0, req['device_id']))
        return dict(req)

def get_recent_generations(device_id, limit=10):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM generations WHERE device_id = ? 
            ORDER BY generated_at DESC LIMIT ?
        """, (device_id, limit)).fetchall()
        return [dict(r) for r in rows]

def get_stats():
    with get_db() as conn:
        pending_vip = conn.execute("SELECT COUNT(*) as c FROM vip_requests WHERE status = 'pending'").fetchone()['c']
        total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()['c']
        verified = conn.execute("SELECT COUNT(*) as c FROM users WHERE verified = 1").fetchone()['c']
        vip = conn.execute("SELECT COUNT(*) as c FROM users WHERE vip = 1").fetchone()['c']
        total_gen = conn.execute("SELECT COUNT(*) as c FROM generations").fetchone()['c']
        pending_appeals = conn.execute("SELECT COUNT(*) as c FROM appeals WHERE status = 'pending'").fetchone()['c']
        banned = conn.execute("SELECT COUNT(*) as c FROM bans WHERE status = 'active'").fetchone()['c']
        today_visitors = conn.execute("""
            SELECT COUNT(*) as c FROM users 
            WHERE date(last_login) = date('now')
        """).fetchone()['c']
        return {
            'total_users': total_users,
            'verified_users': verified,
            'vip_users': vip,
            'total_generations': total_gen,
            'pending_appeals': pending_appeals,
            'banned_devices': banned,
            'today_visitors': today_visitors,
            'pending_vip_requests': pending_vip
        }

# Initialize on import
if __name__ == '__main__':
    init_db()
