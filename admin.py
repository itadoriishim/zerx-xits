"""
ZERX XIT - Admin Blueprint
==========================
All admin-only API endpoints for dashboard management.
"""
import os
import sys
import base64
import hmac
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, session, Response
from werkzeug.security import check_password_hash, generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from database import (
    get_db, get_settings, update_settings, get_stats, get_or_create_user,
    is_banned, ban_device, unban_device, get_all_brands, get_models_by_brand,
    get_device_by_brand_model, log_activity, get_vip_requests, set_vip_request_status,
    get_vip_request
)

admin_bp = Blueprint('admin_api', __name__)

# ─── Auth Helpers ───────────────────────────────────────────────────
ADMIN_PASSWORD_HASH = config.ADMIN_PASSWORD_HASH or generate_password_hash(config.ADMIN_PASSWORD)
ADMIN_SESSION_HOURS = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# {ip: [failed_count, locked_until]}
_LOGIN_ATTEMPTS = {}

def _lockout_remaining(ip):
    entry = _LOGIN_ATTEMPTS.get(ip)
    if not entry or not entry[1]:
        return 0
    remaining = (entry[1] - datetime.utcnow()).total_seconds()
    if remaining <= 0:
        _LOGIN_ATTEMPTS.pop(ip, None)
        return 0
    return int(remaining)

def _register_failure(ip):
    count, _ = _LOGIN_ATTEMPTS.get(ip, (0, None))
    count += 1
    locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES) if count >= MAX_LOGIN_ATTEMPTS else None
    _LOGIN_ATTEMPTS[ip] = (count, locked_until)

def _session_expired():
    started = session.get('admin_login_time')
    if not started:
        return True
    try:
        return datetime.utcnow() - datetime.fromisoformat(started) > timedelta(hours=ADMIN_SESSION_HOURS)
    except ValueError:
        return True

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({"error": "Unauthorized"}), 401
        if _session_expired():
            session.pop('admin_logged_in', None)
            session.pop('admin_login_time', None)
            return jsonify({"error": "Session expired"}), 401
        return f(*args, **kwargs)
    return decorated

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'

# ─── Auth Routes ────────────────────────────────────────────────────
@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    ip = get_client_ip()

    locked_for = _lockout_remaining(ip)
    if locked_for:
        return jsonify({
            "error": f"Too many failed attempts. Try again in {locked_for // 60 + 1} minute(s)."
        }), 429

    username_ok = hmac.compare_digest(username.lower(), config.ADMIN_USERNAME.lower())
    if username_ok and check_password_hash(ADMIN_PASSWORD_HASH, password):
        session.clear()
        session['admin_logged_in'] = True
        session['admin_login_time'] = datetime.utcnow().isoformat()
        _LOGIN_ATTEMPTS.pop(ip, None)
        log_activity('ADMIN', 'admin_login', f"IP: {ip}", ip)
        return jsonify({"success": True, "message": "Logged in"})

    _register_failure(ip)
    log_activity('ADMIN', 'admin_login_fail', f"User: {username}, IP: {ip}", ip)
    return jsonify({"error": "Invalid credentials"}), 401

@admin_bp.route('/logout', methods=['POST'])
@require_admin
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_login_time', None)
    return jsonify({"success": True, "message": "Logged out"})

@admin_bp.route('/check', methods=['GET'])
def check_admin():
    return jsonify({"logged_in": bool(session.get('admin_logged_in')) and not _session_expired()})

# ─── Dashboard ──────────────────────────────────────────────────────
@admin_bp.route('/dashboard', methods=['GET'])
@require_admin
def admin_dashboard():
    stats = get_stats()

    with get_db() as conn:
        # Recent activity
        recent = conn.execute("""
            SELECT * FROM activity_log ORDER BY created_at DESC LIMIT 20
        """).fetchall()
        stats['recent_activity'] = [dict(r) for r in recent]

        # Recent users
        users = conn.execute("""
            SELECT * FROM users ORDER BY created_at DESC LIMIT 20
        """).fetchall()
        stats['recent_users'] = [dict(r) for r in users]

        # Popular phones
        phones = conn.execute("""
            SELECT brand, model, COUNT(*) as count FROM generations 
            GROUP BY brand, model ORDER BY count DESC LIMIT 10
        """).fetchall()
        stats['popular_phones'] = [dict(r) for r in phones]

        # Popular play styles
        styles = conn.execute("""
            SELECT play_style, COUNT(*) as count FROM generations 
            GROUP BY play_style ORDER BY count DESC
        """).fetchall()
        stats['popular_styles'] = [dict(r) for r in styles]

        # Daily generations (last 7 days)
        daily = conn.execute("""
            SELECT date(generated_at) as day, COUNT(*) as count 
            FROM generations 
            WHERE generated_at >= date('now', '-7 days')
            GROUP BY date(generated_at) ORDER BY day
        """).fetchall()
        stats['daily_generations'] = [dict(r) for r in daily]

    return jsonify({"success": True, "stats": stats})

# ─── User Management ────────────────────────────────────────────────
@admin_bp.route('/users', methods=['GET'])
@require_admin
def list_users():
    search = request.args.get('search', '')
    with get_db() as conn:
        if search:
            rows = conn.execute("""
                SELECT * FROM users WHERE 
                zerx_id LIKE ? OR device_id LIKE ? OR brand LIKE ? OR model LIKE ?
                ORDER BY created_at DESC
            """, (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
        else:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 100").fetchall()
    return jsonify({"users": [dict(r) for r in rows]})

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user(user_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return jsonify({"error": "User not found"}), 404
        user = dict(row)
        # Get generations
        gens = conn.execute("SELECT * FROM generations WHERE device_id = ? ORDER BY generated_at DESC", 
                          (user['device_id'],)).fetchall()
        user['generations'] = [dict(r) for r in gens]
    return jsonify({"user": user})

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return jsonify({"success": True})

@admin_bp.route('/users/<int:user_id>/verify', methods=['POST'])
@require_admin
def toggle_verify(user_id):
    data = request.get_json() or {}
    verified = 1 if data.get('verified') else 0
    with get_db() as conn:
        conn.execute("UPDATE users SET verified = ? WHERE id = ?", (verified, user_id))
    return jsonify({"success": True})

@admin_bp.route('/users/<int:user_id>/vip', methods=['POST'])
@require_admin
def toggle_vip(user_id):
    data = request.get_json() or {}
    vip = 1 if data.get('vip') else 0
    with get_db() as conn:
        conn.execute("UPDATE users SET vip = ? WHERE id = ?", (vip, user_id))
    return jsonify({"success": True})

# ─── Ban Management ─────────────────────────────────────────────────
@admin_bp.route('/bans', methods=['GET'])
@require_admin
def list_bans():
    status = request.args.get('status', 'active')
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM bans WHERE status = ? ORDER BY created_at DESC
        """, (status,)).fetchall()
    return jsonify({"bans": [dict(r) for r in rows]})

@admin_bp.route('/bans/unban', methods=['POST'])
@require_admin
def admin_unban():
    data = request.get_json() or {}
    device_id = data.get('device_id', '')
    if not device_id:
        return jsonify({"error": "Device ID required"}), 400
    unban_device(device_id)
    log_activity('ADMIN', 'unban', f"Device: {device_id}", get_client_ip())
    return jsonify({"success": True, "message": "Device unbanned"})

@admin_bp.route('/bans/ban', methods=['POST'])
@require_admin
def admin_ban():
    data = request.get_json() or {}
    device_id = data.get('device_id', '')
    reason = data.get('reason', 'Manual ban by admin')
    if not device_id:
        return jsonify({"error": "Device ID required"}), 400
    user = get_or_create_user(device_id)
    ban_device(device_id, user.get('zerx_id', 'UNKNOWN'), reason)
    log_activity('ADMIN', 'ban', f"Device: {device_id}, Reason: {reason}", get_client_ip())
    return jsonify({"success": True, "message": "Device banned"})

# ─── VIP Requests ───────────────────────────────────────────────
@admin_bp.route('/vip-requests', methods=['GET'])
@require_admin
def list_vip_requests():
    status = request.args.get('status', 'pending')
    return jsonify({"requests": get_vip_requests(status)})

@admin_bp.route('/vip-requests/<int:request_id>/receipt', methods=['GET'])
@require_admin
def vip_request_receipt(request_id):
    """Serve the uploaded payment receipt to the admin only."""
    req = get_vip_request(request_id)
    if not req or not req.get('receipt_data'):
        return jsonify({"error": "No receipt uploaded"}), 404
    try:
        blob = base64.b64decode(req['receipt_data'])
    except (ValueError, TypeError):
        return jsonify({"error": "Receipt could not be read"}), 500
    return Response(blob, mimetype=req.get('receipt_mime') or 'application/octet-stream',
                    headers={'Cache-Control': 'no-store'})

@admin_bp.route('/vip-requests/<int:request_id>/approve', methods=['POST'])
@require_admin
def approve_vip_request(request_id):
    req = set_vip_request_status(request_id, 'approved')
    if not req:
        return jsonify({"error": "Request not found"}), 404
    log_activity('ADMIN', 'vip_approve', f"ZERX ID: {req['zerx_id']}", get_client_ip())
    return jsonify({"success": True, "message": "VIP activated for user"})

@admin_bp.route('/vip-requests/<int:request_id>/reject', methods=['POST'])
@require_admin
def reject_vip_request(request_id):
    req = set_vip_request_status(request_id, 'rejected')
    if not req:
        return jsonify({"error": "Request not found"}), 404
    log_activity('ADMIN', 'vip_reject', f"ZERX ID: {req['zerx_id']}", get_client_ip())
    return jsonify({"success": True, "message": "VIP request rejected"})

# ─── Appeals ────────────────────────────────────────────────────────
@admin_bp.route('/appeals', methods=['GET'])
@require_admin
def list_appeals():
    status = request.args.get('status', 'pending')
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM appeals WHERE status = ? ORDER BY created_at DESC
        """, (status,)).fetchall()
    return jsonify({"appeals": [dict(r) for r in rows]})

@admin_bp.route('/appeals/<int:appeal_id>/approve', methods=['POST'])
@require_admin
def approve_appeal(appeal_id):
    with get_db() as conn:
        appeal = conn.execute("SELECT * FROM appeals WHERE id = ?", (appeal_id,)).fetchone()
        if not appeal:
            return jsonify({"error": "Appeal not found"}), 404
        conn.execute("UPDATE appeals SET status = 'approved' WHERE id = ?", (appeal_id,))
        unban_device(appeal['device_id'])
    log_activity('ADMIN', 'appeal_approve', f"ZERX ID: {appeal['zerx_id']}", get_client_ip())
    return jsonify({"success": True, "message": "Appeal approved, device unbanned"})

@admin_bp.route('/appeals/<int:appeal_id>/reject', methods=['POST'])
@require_admin
def reject_appeal(appeal_id):
    with get_db() as conn:
        conn.execute("UPDATE appeals SET status = 'rejected' WHERE id = ?", (appeal_id,))
    log_activity('ADMIN', 'appeal_reject', f"Appeal ID: {appeal_id}", get_client_ip())
    return jsonify({"success": True, "message": "Appeal rejected"})

# ─── Settings ───────────────────────────────────────────────────────
@admin_bp.route('/settings', methods=['GET'])
@require_admin
def admin_get_settings():
    return jsonify({"success": True, "settings": get_settings()})

@admin_bp.route('/settings', methods=['POST'])
@require_admin
def admin_update_settings():
    data = request.get_json() or {}
    update_settings(**data)
    log_activity('ADMIN', 'settings_update', str(data), get_client_ip())
    return jsonify({"success": True, "message": "Settings updated"})

# ─── Device Database ────────────────────────────────────────────────
@admin_bp.route('/devices', methods=['GET'])
@require_admin
def list_devices():
    brand = request.args.get('brand', '')
    with get_db() as conn:
        if brand:
            rows = conn.execute("SELECT * FROM devices WHERE brand = ? ORDER BY model", (brand,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM devices ORDER BY brand, model").fetchall()
    return jsonify({"devices": [dict(r) for r in rows]})

@admin_bp.route('/devices', methods=['POST'])
@require_admin
def add_device():
    data = request.get_json() or {}
    required = ['brand', 'model']
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} required"}), 400

    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO devices 
            (brand, model, processor, gpu, ram, android_version, refresh_rate,
             performance_score, gaming_score, release_year, architecture, battery_size, screen_resolution)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('brand'), data.get('model'), data.get('processor', ''),
            data.get('gpu', ''), data.get('ram', ''), data.get('android_version', ''),
            data.get('refresh_rate', ''), data.get('performance_score', 50),
            data.get('gaming_score', 50), data.get('release_year', 2024),
            data.get('architecture', ''), data.get('battery_size', ''),
            data.get('screen_resolution', '')
        ))
    return jsonify({"success": True, "message": "Device added"})

@admin_bp.route('/devices/<int:device_id>', methods=['PUT'])
@require_admin
def edit_device(device_id):
    data = request.get_json() or {}
    allowed = ['brand', 'model', 'processor', 'gpu', 'ram', 'android_version',
               'refresh_rate', 'performance_score', 'gaming_score', 'release_year',
               'architecture', 'battery_size', 'screen_resolution']
    sets = []
    vals = []
    for k, v in data.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            vals.append(v)
    if sets:
        vals.append(device_id)
        with get_db() as conn:
            conn.execute(f"UPDATE devices SET {', '.join(sets)} WHERE id = ?", vals)
    return jsonify({"success": True, "message": "Device updated"})

@admin_bp.route('/devices/<int:device_id>', methods=['DELETE'])
@require_admin
def delete_device(device_id):
    with get_db() as conn:
        conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    return jsonify({"success": True, "message": "Device deleted"})

@admin_bp.route('/devices/import', methods=['POST'])
@require_admin
def bulk_import_devices():
    data = request.get_json() or {}
    devices = data.get('devices', [])
    if not devices:
        return jsonify({"error": "No devices provided"}), 400

    with get_db() as conn:
        for d in devices:
            conn.execute("""
                INSERT OR REPLACE INTO devices 
                (brand, model, processor, gpu, ram, android_version, refresh_rate,
                 performance_score, gaming_score, release_year, architecture, battery_size, screen_resolution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d.get('brand'), d.get('model'), d.get('processor', ''),
                d.get('gpu', ''), d.get('ram', ''), d.get('android_version', ''),
                d.get('refresh_rate', ''), d.get('performance_score', 50),
                d.get('gaming_score', 50), d.get('release_year', 2024),
                d.get('architecture', ''), d.get('battery_size', ''),
                d.get('screen_resolution', '')
            ))
    return jsonify({"success": True, "message": f"Imported {len(devices)} devices"})

# ─── Analytics ──────────────────────────────────────────────────────
@admin_bp.route('/analytics', methods=['GET'])
@require_admin
def get_analytics():
    with get_db() as conn:
        # Daily visitors (last 14 days)
        visitors = conn.execute("""
            SELECT date(last_login) as day, COUNT(*) as count 
            FROM users 
            WHERE last_login >= date('now', '-14 days')
            GROUP BY date(last_login) ORDER BY day
        """).fetchall()

        # VIP sales (simulated by VIP user creation dates)
        vip_sales = conn.execute("""
            SELECT date(created_at) as day, COUNT(*) as count 
            FROM users 
            WHERE vip = 1 AND created_at >= date('now', '-14 days')
            GROUP BY date(created_at) ORDER BY day
        """).fetchall()

        # Verification success rate
        total = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()['c']
        verified = conn.execute("SELECT COUNT(*) as c FROM users WHERE verified = 1").fetchone()['c']

        # Appeal stats
        appeals_total = conn.execute("SELECT COUNT(*) as c FROM appeals").fetchone()['c']
        appeals_pending = conn.execute("SELECT COUNT(*) as c FROM appeals WHERE status = 'pending'").fetchone()['c']
        appeals_approved = conn.execute("SELECT COUNT(*) as c FROM appeals WHERE status = 'approved'").fetchone()['c']

    return jsonify({
        "daily_visitors": [dict(r) for r in visitors],
        "vip_sales": [dict(r) for r in vip_sales],
        "verification_rate": round((verified / total * 100), 2) if total > 0 else 0,
        "appeals": {
            "total": appeals_total,
            "pending": appeals_pending,
            "approved": appeals_approved,
            "rejected": appeals_total - appeals_pending - appeals_approved
        }
    })
