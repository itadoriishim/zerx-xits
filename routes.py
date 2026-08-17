"""
ZERX XIT - API Routes
=====================
All public API endpoints for the platform.
"""
import os
import sys
import json
import base64
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, session

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from database import (
    get_db, get_settings, get_or_create_user, is_banned, ban_device,
    get_device_by_brand_model, get_models_by_brand, get_all_brands,
    save_generation, get_recent_generations, update_xit_prefs, get_user_xit_prefs,
    log_activity, search_devices, get_latest_generation,
    create_vip_request, get_vip_request_status
)
from engine import SensitivityEngine
from ai_engine import AIEngine
from verification import VerificationManager

MAX_CODE_ATTEMPTS = 3

api_bp = Blueprint('api', __name__)

# ─── Helpers ────────────────────────────────────────────────────────
def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'

def require_auth():
    device_id = session.get('device_id')
    if not device_id:
        return None, jsonify({"error": "No session"}), 401
    user = get_or_create_user(device_id)
    ban = is_banned(device_id)
    if ban:
        return None, jsonify({"error": "Banned", "zerx_id": ban['zerx_id']}), 403
    return user, None, 200

# ─── Device Detection ───────────────────────────────────────────────
@api_bp.route('/device', methods=['GET'])
def get_device_info():
    """Return detected device info from headers + JS will supplement."""
    user_agent = request.headers.get('User-Agent', '')
    platform = request.headers.get('Sec-Ch-Ua-Platform', 'Unknown')

    # Basic detection
    os_name = 'Unknown'
    if 'Android' in user_agent:
        os_name = 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        os_name = 'iOS'
    elif 'Windows' in user_agent:
        os_name = 'Windows'
    elif 'Mac' in user_agent:
        os_name = 'Mac'
    elif 'Linux' in user_agent:
        os_name = 'Linux'

    browser = 'Unknown'
    if 'Chrome' in user_agent and 'Edg' not in user_agent:
        browser = 'Chrome'
    elif 'Edg' in user_agent:
        browser = 'Edge'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'SamsungBrowser' in user_agent:
        browser = 'Samsung Browser'
    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
        browser = 'Safari'

    return jsonify({
        "os": os_name,
        "browser": browser,
        "platform": platform.strip('"'),
        "user_agent": user_agent,
        "language": request.headers.get('Accept-Language', 'en').split(',')[0],
        "timezone": request.headers.get('X-Timezone', 'UTC')
    })

@api_bp.route('/device/brands', methods=['GET'])
def get_brands():
    """Return all supported brands."""
    brands = get_all_brands()
    return jsonify({"brands": brands})

@api_bp.route('/device/models', methods=['GET'])
def get_models():
    """Return models for a brand."""
    brand = request.args.get('brand', '')
    if not brand:
        return jsonify({"error": "Brand required"}), 400
    models = get_models_by_brand(brand)
    return jsonify({"models": models})

@api_bp.route('/device/search', methods=['GET'])
def device_search():
    """Search all supported devices by brand or model name."""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({"devices": []})
    return jsonify({"devices": search_devices(query, limit=40)})

@api_bp.route('/device/details', methods=['GET'])
def get_device_details():
    """Return full device specs from database."""
    brand = request.args.get('brand', '')
    model = request.args.get('model', '')
    if not brand or not model:
        return jsonify({"error": "Brand and model required"}), 400
    device = get_device_by_brand_model(brand, model)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    return jsonify(device)

# ─── Verification ───────────────────────────────────────────────────
@api_bp.route('/share-message', methods=['GET'])
def get_share_message():
    """Return the official share message with dynamic links."""
    settings = get_settings()
    device_id = session.get('device_id', '')
    user = get_or_create_user(device_id)

    del user  # session side effects only

    message = f"""ZERX XIT — Free Fire Sensitivity & Optimization

Get device-optimized sensitivity settings for free.

WhatsApp Channel:
{settings.get('whatsapp_channel', '')}

Telegram Channel:
{settings.get('telegram_main', '')}

Join now ✅"""

    return jsonify({
        "message": message,
        "verification_code": settings.get('verification_code', 'ZERX FOR 2027'),
        "whatsapp": settings.get('whatsapp_channel', ''),
        "telegram_main": settings.get('telegram_main', ''),
        "telegram_backup": settings.get('telegram_backup', '')
    })

@api_bp.route('/verify/status', methods=['GET'])
def verification_status():
    """Current server-side progress of the join / share / code steps."""
    user, error, code = require_auth()
    if error:
        return error, code
    return jsonify(VerificationManager(session.get('device_id', '')).status())

@api_bp.route('/verify/join', methods=['POST'])
def verification_join():
    """Record that the user opened the channels."""
    user, error, code = require_auth()
    if error:
        return error, code
    return jsonify({"success": True, "status": VerificationManager(session.get('device_id', '')).mark_joined()})

@api_bp.route('/verify/share', methods=['POST'])
def verification_share():
    """Count one completed share (server-side, rate limited)."""
    user, error, code = require_auth()
    if error:
        return error, code
    manager = VerificationManager(session.get('device_id', ''))
    status, accepted = manager.add_share()
    if not accepted and not status['joined']:
        return jsonify({"error": "Open the channels first", "status": status}), 400
    if not accepted:
        return jsonify({"error": "Wait a moment before sharing again", "status": status}), 429
    return jsonify({"success": True, "status": status})

@api_bp.route('/verify', methods=['POST'])
def verify_code():
    """Verify the user-entered code. A success is valid for one generation."""
    data = request.get_json() or {}
    device_id = session.get('device_id', '')
    user = get_or_create_user(device_id)

    # Banned devices cannot verify
    ban = is_banned(device_id)
    if ban:
        return jsonify({
            "success": False, "banned": True, "zerx_id": ban['zerx_id'],
            "message": "This device is banned. Submit an appeal to regain access."
        }), 403

    manager = VerificationManager(device_id)
    status = manager.status()
    if not status['joined'] or not status['shares_complete']:
        return jsonify({
            "success": False,
            "message": "Complete the join and share steps before entering the code",
            "status": status
        }), 400

    submitted_code = data.get('code', '').strip().upper()
    settings = get_settings()
    correct_code = settings.get('verification_code', 'ZERX FOR 2027').strip().upper()

    log_activity(device_id, 'verify_attempt', 'Code submitted', get_client_ip())

    if submitted_code == correct_code:
        session['code_attempts'] = 0
        manager.complete()
        log_activity(device_id, 'verify_success', 'Verification completed', get_client_ip())
        return jsonify({"success": True, "message": "Verification complete"})

    attempts = int(session.get('code_attempts', 0)) + 1
    session['code_attempts'] = attempts
    remaining = MAX_CODE_ATTEMPTS - attempts
    if remaining > 0:
        return jsonify({
            "success": False,
            "message": f"Incorrect code. {remaining} attempt(s) left before this device is blocked.",
            "attempts_left": remaining
        }), 400

    zerx_id = user.get('zerx_id', f"ZX-{secrets.token_hex(4).upper()}")
    ban_device(device_id, zerx_id, "Invalid Verification Code")
    session['code_attempts'] = 0
    log_activity(device_id, 'verify_fail_ban', f"ZERX ID: {zerx_id}", get_client_ip())
    return jsonify({
        "success": False,
        "banned": True,
        "zerx_id": zerx_id,
        "message": "Too many incorrect codes. Device blocked."
    }), 403

@api_bp.route('/check-verification', methods=['GET'])
def check_verification():
    """Check if current device is verified."""
    device_id = session.get('device_id', '')
    user = get_or_create_user(device_id)
    ban = is_banned(device_id)
    if ban:
        return jsonify({"verified": False, "banned": True, "zerx_id": ban['zerx_id']})
    return jsonify({
        "verified": bool(user.get('verified')),
        "vip": bool(user.get('vip')),
        "banned": False,
        "device_id": device_id,
        "zerx_id": user.get('zerx_id', '')
    })

# ─── Generation ─────────────────────────────────────────────────────
@api_bp.route('/generate', methods=['POST'])
def generate_sensitivity():
    """Main sensitivity generation endpoint."""
    user, error, code = require_auth()
    if error:
        return error, code
    if not user.get('verified') and not user.get('vip'):
        return jsonify({"error": "Verification required"}), 403

    data = request.get_json() or {}
    device_id = session.get('device_id', '')

    # Extract device info
    option = data.get('option', 'this')  # 'this' or 'other'
    play_style = data.get('play_style', 'Balanced')
    tune = data.get('tune', 0)
    screen = data.get('screen') if isinstance(data.get('screen'), dict) else None

    device_info = {}
    if option == 'other':
        brand = data.get('brand', '')
        model = data.get('model', '')
        db_device = get_device_by_brand_model(brand, model)
        if db_device:
            device_info = db_device
        else:
            # Manual fallback
            device_info = {
                'brand': brand,
                'model': model,
                'processor': data.get('processor', 'Unknown'),
                'gpu': data.get('gpu', 'Unknown'),
                'ram': data.get('ram', '4GB'),
                'android_version': data.get('android_version', 'Unknown'),
                'refresh_rate': data.get('refresh_rate', '60Hz'),
                'performance_score': 50,
                'gaming_score': 50
            }
    else:
        # This phone - use detected + database match
        detected = data.get('detected', {})
        brand = detected.get('brand', 'Unknown')
        model = detected.get('model', 'Unknown')
        db_device = get_device_by_brand_model(brand, model)
        if db_device:
            device_info = db_device
        else:
            device_info = {
                'brand': brand,
                'model': model,
                'processor': detected.get('processor', 'Unknown'),
                'gpu': detected.get('gpu', 'Unknown'),
                'ram': detected.get('ram', '4GB'),
                'android_version': detected.get('os', 'Unknown'),
                'refresh_rate': detected.get('refresh_rate', '60Hz'),
                'performance_score': detected.get('performance_score', 50),
                'gaming_score': detected.get('gaming_score', 50)
            }

    # Sensitivity values always come from the local deterministic engine so a
    # generation can never fail because an external service is unavailable.
    engine = SensitivityEngine()
    try:
        result = engine.generate(device_info, play_style, vip=bool(user.get('vip')),
                                 tune=tune, screen=screen)
    except Exception:
        return jsonify({"error": "Could not calculate settings for this device. Try another model."}), 500

    # Written guidance: local by default, Gemini only when a key is configured.
    settings = get_settings()
    ai_data = engine.fallback_tips(device_info, play_style, vip=bool(user.get('vip')))
    result['ai_optimized'] = 0
    if settings.get('ai_enabled') and config.GEMINI_API_KEY:
        try:
            ai = AIEngine()
            ai_data = ai.optimize(device_info, result, play_style, vip=bool(user.get('vip')))
            result['ai_optimized'] = 1
        except Exception:
            pass  # guidance falls back to the local tips

    result['ai_data'] = ai_data
    result['device_info'] = device_info
    result['play_style'] = play_style
    result['vip'] = bool(user.get('vip'))

    # Save to database
    save_generation(
        device_id,
        device_info.get('brand', 'Unknown'),
        device_info.get('model', 'Unknown'),
        play_style,
        result
    )

    # Update user device info
    with get_db() as conn:
        conn.execute("""
            UPDATE users SET brand=?, model=?, processor=?, gpu=?, ram=?,
            android_version=?, refresh_rate=?, play_style=? WHERE device_id=?
        """, (
            device_info.get('brand'), device_info.get('model'),
            device_info.get('processor'), device_info.get('gpu'),
            device_info.get('ram'), device_info.get('android_version'),
            device_info.get('refresh_rate'), play_style, device_id
        ))

    log_activity(device_id, 'generate', f"{device_info.get('brand')} {device_info.get('model')} - {play_style}", get_client_ip())

    # Verification is consumed per generation — non-VIP users must verify
    # again before their next generation.
    if not user.get('vip'):
        VerificationManager(device_id).reset()

    return jsonify({"success": True, "result": result})

# ─── Result ─────────────────────────────────────────────────────────
@api_bp.route('/result', methods=['GET'])
def get_result():
    """Return last generated result."""
    user, error, code = require_auth()
    if error:
        return error, code
    device_id = session.get('device_id', '')
    gen = get_latest_generation(device_id)
    if not gen or not gen.get('result_json'):
        return jsonify({"error": "No result found"}), 404
    try:
        result = json.loads(gen['result_json'])
    except (ValueError, TypeError):
        return jsonify({"error": "No result found"}), 404
    result.setdefault('generated_at', gen.get('generated_at'))
    result.setdefault('zerx_id', user.get('zerx_id'))
    return jsonify({"success": True, "result": result})

# ─── XIT Features ───────────────────────────────────────────────────
@api_bp.route('/xit/prefs', methods=['GET'])
def get_xit_prefs():
    """Get XIT preferences for device."""
    user, error, code = require_auth()
    if error:
        return error, code
    device_id = session.get('device_id', '')
    prefs = get_user_xit_prefs(device_id)
    return jsonify({"success": True, "prefs": prefs, "vip": bool(user.get('vip'))})

@api_bp.route('/xit/prefs', methods=['POST'])
def save_xit_prefs():
    """Save XIT preferences."""
    user, error, code = require_auth()
    if error:
        return error, code
    if not user.get('vip'):
        return jsonify({"error": "VIP required", "vip_required": True}), 403
    device_id = session.get('device_id', '')
    data = request.get_json() or {}
    update_xit_prefs(device_id, **data)
    return jsonify({"success": True, "message": "Preferences saved"})

# Step-by-step guides. A website cannot change Android system settings, so each
# VIP feature returns the exact manual steps for the user's own device instead.
XIT_GUIDES = {
    'xit_boost': {
        'title': 'XIT Performance Boost',
        'steps': [
            'Open Settings > Apps > Free Fire > Battery and choose Unrestricted.',
            'Enable the manufacturer game mode (Game Booster, Game Space or Game Turbo).',
            'Close background apps before a match and keep at least 1.5GB RAM free.',
            'Set Free Fire graphics to Smooth and frame rate to the highest your device allows.',
        ],
    },
    'touch_optimization': {
        'title': 'Touch Response',
        'steps': [
            'Enable Developer Options: Settings > About phone > tap Build number 7 times.',
            'In Developer Options turn on "Show taps" briefly to confirm your thumb placement.',
            'Disable screen protectors with air bubbles — they add real touch latency.',
            'Turn on the high touch sampling / gaming touch option if your device has one.',
        ],
    },
    'fps_optimization': {
        'title': 'Frame Rate Stability',
        'steps': [
            'Developer Options > Animation scales: set all three to 0.5x.',
            'Disable adaptive brightness and battery saver while playing.',
            'Keep the phone below 80% charge during long sessions to limit throttling.',
            'Lower in-game shadows and high-detail effects on chipsets below Snapdragon 7-series.',
        ],
    },
    'low_ping_mode': {
        'title': 'Network Stability',
        'steps': [
            'Use the closest Free Fire server region to your location.',
            'Prefer 5GHz Wi-Fi; on mobile data lock the network to 4G/LTE only.',
            'Disable automatic app updates and cloud backup while playing.',
            'Turn off VPNs unless your ISP route to the game server is genuinely poor.',
        ],
    },
    'gaming_mode': {
        'title': 'Distraction-Free Gaming',
        'steps': [
            'Enable Do Not Disturb and block call pop-ups in your game mode settings.',
            'Turn off gesture navigation edge swipes or enable full-screen gesture lock.',
            'Set the screen refresh rate to High/Adaptive instead of Standard.',
        ],
    },
    'performance_mode': {
        'title': 'Sustained Performance',
        'steps': [
            'Enable High Performance mode in Settings > Battery.',
            'Clear the Free Fire cache monthly: Settings > Apps > Free Fire > Storage.',
            'Keep at least 8GB of free storage so the game can write assets without stutter.',
        ],
    },
    'aim_assist_mode': {
        'title': 'Aim Consistency Drill',
        'steps': [
            'Apply your generated sensitivity, then play 10 minutes in training only.',
            'Adjust general sensitivity in steps of 3 until a 180° turn is one thumb swipe.',
            'Adjust red dot last — it should track a moving target without overshooting.',
        ],
    },
    'sensitivity_lock': {
        'title': 'Keep Your Settings',
        'steps': [
            'Save the generated profile from the Result page before changing anything.',
            'Re-apply after every Free Fire update — patches can reset sensitivity.',
        ],
    },
}

@api_bp.route('/xit/guide', methods=['POST'])
def xit_guide():
    """Return the manual steps for a XIT feature. VIP only, enforced server-side."""
    user, error, code = require_auth()
    if error:
        return error, code
    if not user.get('vip'):
        return jsonify({"error": "VIP required", "vip_required": True}), 403

    data = request.get_json() or {}
    feature = (data.get('feature') or '').strip()
    guide = XIT_GUIDES.get(feature)
    if not guide:
        return jsonify({"error": "Unknown feature"}), 404

    device = f"{user.get('brand') or ''} {user.get('model') or ''}".strip() or 'your device'
    return jsonify({
        "success": True,
        "feature": feature,
        "title": guide['title'],
        "device": device,
        "steps": guide['steps'],
        "note": "These steps are applied on the device itself — a website cannot change Android system settings for you."
    })

@api_bp.route('/xit/recent', methods=['GET'])
def get_xit_recent():
    """Get recent generations for XIT profile."""
    user, error, code = require_auth()
    if error:
        return error, code
    device_id = session.get('device_id', '')
    recent = get_recent_generations(device_id, limit=10)
    return jsonify({"success": True, "generations": recent})

# ─── Profile ────────────────────────────────────────────────────────
@api_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get full profile data."""
    device_id = session.get('device_id', '')
    user = get_or_create_user(device_id)
    ban = is_banned(device_id)
    prefs = get_user_xit_prefs(device_id)
    recent = get_recent_generations(device_id, limit=5)
    return jsonify({
        "user": user,
        "banned": bool(ban),
        "prefs": prefs,
        "recent_generations": recent
    })

# ─── VIP Activation ─────────────────────────────────────────────
@api_bp.route('/vip/request', methods=['POST'])
def submit_vip_request():
    """Submit a VIP activation request with the payment receipt."""
    user, error, code = require_auth()
    if error:
        return error, code
    if user.get('vip'):
        return jsonify({"success": True, "status": "active", "message": "VIP is already active"})

    device_id = session.get('device_id', '')

    if request.files:
        reference = (request.form.get('reference') or '').strip()[:200]
        sender = (request.form.get('sender_name') or '').strip()[:100]
        upload = request.files.get('receipt')
    else:
        data = request.get_json() or {}
        reference = (data.get('reference') or '').strip()[:200]
        sender = (data.get('sender_name') or '').strip()[:100]
        upload = None

    if not sender:
        return jsonify({"error": "Enter the name used to make the payment"}), 400

    receipt_mime = None
    receipt_data = None
    if upload and upload.filename:
        mime = (upload.mimetype or '').lower()
        if mime not in config.ALLOWED_RECEIPT_TYPES:
            return jsonify({"error": "Receipt must be a PNG, JPG, WEBP image or a PDF"}), 400
        blob = upload.read(config.MAX_RECEIPT_BYTES + 1)
        if len(blob) > config.MAX_RECEIPT_BYTES:
            return jsonify({"error": "Receipt is too large. Maximum size is 4MB."}), 400
        if not blob:
            return jsonify({"error": "The receipt file is empty"}), 400
        receipt_mime = mime
        receipt_data = base64.b64encode(blob).decode('ascii')

    req_id, created = create_vip_request(device_id, user.get('zerx_id', ''), reference, sender,
                                         receipt_mime, receipt_data)
    log_activity(device_id, 'vip_request', f"Request #{req_id} from {sender}", get_client_ip())
    return jsonify({
        "success": True,
        "status": "pending",
        "has_receipt": bool(receipt_data),
        "message": "Payment submitted. VIP is activated once the admin confirms it." if created
        else "Your request was updated. VIP is activated once the admin confirms it."
    })

@api_bp.route('/vip/status', methods=['GET'])
def vip_status():
    """Return VIP status for current device."""
    device_id = session.get('device_id', '')
    user = get_or_create_user(device_id)
    if user.get('vip'):
        return jsonify({"vip": True, "status": "active"})
    req = get_vip_request_status(device_id)
    return jsonify({
        "vip": False,
        "status": req['status'] if req else 'none',
        "submitted_at": req['created_at'] if req else None
    })

# ─── Appeal ─────────────────────────────────────────────────────────
@api_bp.route('/appeal', methods=['POST'])
def submit_appeal():
    """Submit unban appeal."""
    data = request.get_json() or {}
    device_id = session.get('device_id', '')
    zerx_id = data.get('zerx_id', '')
    message = data.get('message', '')

    if not zerx_id or not message:
        return jsonify({"error": "ZERX ID and message required"}), 400

    with get_db() as conn:
        conn.execute("""
            INSERT INTO appeals (zerx_id, device_id, message, status)
            VALUES (?, ?, ?, 'pending')
        """, (zerx_id, device_id, message))

    log_activity(device_id, 'appeal_submit', f"ZERX ID: {zerx_id}", get_client_ip())
    return jsonify({"success": True, "message": "Appeal submitted"})

# ─── Settings ───────────────────────────────────────────────────────
@api_bp.route('/settings', methods=['GET'])
def get_public_settings():
    """Return public platform settings."""
    settings = get_settings()
    return jsonify({
        "whatsapp_channel": settings.get('whatsapp_channel', ''),
        "whatsapp_channel_2": settings.get('whatsapp_channel_2', ''),
        "telegram_main": settings.get('telegram_main', ''),
        "telegram_backup": settings.get('telegram_backup', ''),
        "telegram_leaks": settings.get('telegram_leaks', ''),
        "admin_whatsapp": settings.get('admin_whatsapp', ''),
        "mediafire_link": settings.get('mediafire_link', ''),
        "setup_video": settings.get('setup_video', ''),
        "vip_price": settings.get('vip_price', '₦2,000'),
        "admin_telegram": settings.get('admin_telegram', '@zerxofficial'),
        "share_count": settings.get('share_count', 5),
        "vip_enabled": bool(settings.get('vip_enabled', 1)),
        "verification_required_every_time": True,
        "payment": {
            "price": settings.get('vip_price', '₦2,000'),
            "accounts": [
                {"number": settings.get('pay1_number', ''), "bank": settings.get('pay1_bank', ''), "name": settings.get('pay1_name', '')},
                {"number": settings.get('pay2_number', ''), "bank": settings.get('pay2_bank', ''), "name": settings.get('pay2_name', '')}
            ]
        }
    })
