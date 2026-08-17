"""
ZERX XIT - Configuration
========================
Central configuration for the entire platform.
"""
import os
import secrets

# ─── Paths ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')

# ─── Flask Core ─────────────────────────────────────────────────────
def _load_secret_key():
    """Use SECRET_KEY env var if set; otherwise persist one to disk so
    sessions survive restarts."""
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    key_file = os.path.join(BASE_DIR, '.instance_secret')
    try:
        if os.path.exists(key_file):
            with open(key_file) as f:
                key = f.read().strip()
                if key:
                    return key
        key = secrets.token_hex(32)
        with open(key_file, 'w') as f:
            f.write(key)
        return key
    except OSError:
        return secrets.token_hex(32)

SECRET_KEY = _load_secret_key()
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

# ─── Database ───────────────────────────────────────────────────────
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ─── Optional AI Assistance ─────────────────────────────────────────
# Sensitivity values are always produced by the local deterministic engine.
# When a Gemini key is configured the platform additionally requests written
# optimization guidance; a failure never blocks a generation.
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_TOKENS = 1024
GEMINI_TIMEOUT = int(os.environ.get('GEMINI_TIMEOUT', '8'))

# ─── Admin Credentials ──────────────────────────────────────────────
# Override with ADMIN_USERNAME / ADMIN_PASSWORD environment variables in
# production. ADMIN_PASSWORD_HASH (a Werkzeug hash) takes priority over
# ADMIN_PASSWORD when both are set.
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'zerx.admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'ZerxXit#Ctrl2027')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')

# ─── Platform Defaults ──────────────────────────────────────────────
DEFAULT_VERIFICATION_CODE = 'ZERX FOR 2027'
DEFAULT_VIP_PRICE = '₦2000'
DEFAULT_SHARE_COUNT = 5

# ─── Security ───────────────────────────────────────────────────────
MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 6MB request limit (receipt uploads)
MAX_RECEIPT_BYTES = 4 * 1024 * 1024
ALLOWED_RECEIPT_TYPES = ('image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'application/pdf')
RATE_LIMIT_DEFAULT = "100 per hour"

# ─── Free Fire Deep Link ────────────────────────────────────────────
FF_PACKAGE_NAME = 'com.dts.freefireth'
FF_DEEP_LINK = f'intent://#Intent;package={FF_PACKAGE_NAME};scheme=freefire;end'
