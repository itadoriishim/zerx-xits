"""
ZERX XIT - Main Application
============================
Flask application factory and core setup.
"""
import os
import secrets
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from database import init_db, get_db, get_settings, get_or_create_user, is_banned, get_stats

# ─── App Factory ────────────────────────────────────────────────────
def create_app():
    app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

    app.config.from_object(config)
    app.secret_key = config.SECRET_KEY
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('FORCE_HTTPS', '1') == '1'
        and not os.environ.get('FLASK_DEBUG'),
        PERMANENT_SESSION_LIFETIME=timedelta(days=180),
        JSON_SORT_KEYS=False,
    )

    # Initialize database
    init_db()

    # ─── Context Processors ─────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {
            'site_name': 'ZERX XIT',
            'current_year': datetime.now().year,
            'primary_color': '#ff1f4d',
            'secondary_color': '#b00020'
        }

    # ─── Before / After Request ─────────────────────────────────────
    @app.before_request
    def before_request():
        # Ensure device_id exists
        if 'device_id' not in session:
            session['device_id'] = f"ZXDEVICE-{secrets.token_hex(8).upper()}"
        session.permanent = True

    @app.after_request
    def after_request(response):
        # Ask Chromium browsers for the high-entropy client hints we use for
        # device detection (the exact model is only sent when requested).
        response.headers.setdefault(
            'Accept-CH',
            'Sec-CH-UA-Model, Sec-CH-UA-Platform, Sec-CH-UA-Platform-Version, '
            'Sec-CH-UA-Arch, Sec-CH-UA-Bitness, Sec-CH-UA-Full-Version-List, Device-Memory')
        response.headers.setdefault('Critical-CH', 'Sec-CH-UA-Model, Sec-CH-UA-Platform-Version')
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        return response

    # ─── Error Handlers ─────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Not found"}), 404
        return render_template('index.html', error="Page not found"), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large. Maximum size is 4MB."}), 413

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    # ─── Routes ─────────────────────────────────────────────────────
    @app.route('/')
    def index():
        device_id = session.get('device_id', '')
        user = get_or_create_user(device_id)
        ban = is_banned(device_id)
        if ban:
            return redirect(url_for('banned_page'))
        settings = get_settings()
        return render_template('index.html', user=user, settings=settings)

    @app.route('/generator')
    def generator():
        # The generator is open to everyone; free users verify inside the page
        # before every generation (enforced server-side by /api/generate).
        device_id = session.get('device_id', '')
        user = get_or_create_user(device_id)
        ban = is_banned(device_id)
        if ban:
            return redirect(url_for('banned_page'))
        settings = get_settings()
        return render_template('generator.html', user=user, settings=settings)

    @app.route('/community')
    def community_page():
        device_id = session.get('device_id', '')
        user = get_or_create_user(device_id)
        ban = is_banned(device_id)
        if ban:
            return redirect(url_for('banned_page'))
        settings = get_settings()
        return render_template('community.html', user=user, settings=settings)

    @app.route('/vip')
    def vip_page():
        device_id = session.get('device_id', '')
        user = get_or_create_user(device_id)
        ban = is_banned(device_id)
        if ban:
            return redirect(url_for('banned_page'))
        settings = get_settings()
        return render_template('vip.html', user=user, settings=settings)

    @app.route('/verify')
    def verify_page():
        device_id = session.get('device_id', '')
        user = get_or_create_user(device_id)
        ban = is_banned(device_id)
        if ban:
            return redirect(url_for('banned_page'))
        settings = get_settings()
        return render_template('verify.html', user=user, settings=settings)

    @app.route('/result')
    def result_page():
        device_id = session.get('device_id', '')
        user = get_or_create_user(device_id)
        ban = is_banned(device_id)
        if ban:
            return redirect(url_for('banned_page'))
        return render_template('result.html', user=user)

    @app.route('/banned')
    def banned_page():
        device_id = session.get('device_id', '')
        ban = is_banned(device_id)
        if not ban:
            return redirect(url_for('index'))
        settings = get_settings()
        return render_template('banned.html', ban=ban, settings=settings)

    @app.route('/xit')
    def xit_page():
        # XIT is visible to everyone; the controls themselves are VIP-only
        # and enforced server-side.
        device_id = session.get('device_id', '')
        user = get_or_create_user(device_id)
        ban = is_banned(device_id)
        if ban:
            return redirect(url_for('banned_page'))
        settings = get_settings()
        return render_template('xit.html', user=user, settings=settings)

    @app.route('/admin-login')
    def admin_login_page():
        return render_template('admin_login.html')

    @app.route('/admin-dashboard')
    def admin_dashboard_page():
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login_page'))
        stats = get_stats()
        settings = get_settings()
        return render_template('admin_dashboard.html', stats=stats, settings=settings)

    # ─── Register Blueprints ────────────────────────────────────────
    from routes import api_bp
    from admin import admin_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    return app

# ─── Run ────────────────────────────────────────────────────────────
app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)