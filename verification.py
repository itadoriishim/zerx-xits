"""
ZERX XIT - Verification Manager
================================
Server-side verification state. Every generation consumes one verification,
so the join/share/code steps must be completed again for the next one.

State lives in the database (not in memory) so it survives restarts and stays
consistent across gunicorn workers.
"""
from datetime import datetime, timedelta

from database import get_db, get_settings

MIN_SECONDS_BETWEEN_SHARES = 3


class VerificationManager:
    """Tracks the join / share / code steps for a single device."""

    def __init__(self, device_id):
        self.device_id = device_id

    # ─── State ──────────────────────────────────────────────────────
    def _row(self):
        with get_db() as conn:
            row = conn.execute("""
                SELECT verified, vip, joined_channels, share_progress, last_share_at
                FROM users WHERE device_id = ?
            """, (self.device_id,)).fetchone()
        return dict(row) if row else {}

    def required_shares(self):
        try:
            return max(1, int(get_settings().get('share_count') or 5))
        except (TypeError, ValueError):
            return 5

    def status(self):
        row = self._row()
        required = self.required_shares()
        shares = int(row.get('share_progress') or 0)
        return {
            'joined': bool(row.get('joined_channels')),
            'shares': shares,
            'required_shares': required,
            'shares_complete': shares >= required,
            'verified': bool(row.get('verified')),
            'vip': bool(row.get('vip')),
        }

    # ─── Steps ──────────────────────────────────────────────────────
    def mark_joined(self):
        with get_db() as conn:
            conn.execute("UPDATE users SET joined_channels = 1 WHERE device_id = ?",
                         (self.device_id,))
        return self.status()

    def add_share(self):
        """Count one completed share. Returns (status, accepted)."""
        row = self._row()
        if not row.get('joined_channels'):
            return self.status(), False

        last = row.get('last_share_at')
        if last:
            try:
                previous = datetime.fromisoformat(str(last))
                if datetime.utcnow() - previous < timedelta(seconds=MIN_SECONDS_BETWEEN_SHARES):
                    return self.status(), False
            except ValueError:
                pass

        required = self.required_shares()
        shares = min(required, int(row.get('share_progress') or 0) + 1)
        with get_db() as conn:
            conn.execute("""
                UPDATE users SET share_progress = ?, last_share_at = ? WHERE device_id = ?
            """, (shares, datetime.utcnow().isoformat(timespec='seconds'), self.device_id))
        return self.status(), True

    def can_submit_code(self):
        status = self.status()
        return status['joined'] and status['shares_complete']

    def complete(self):
        """Mark the device verified for exactly one generation."""
        with get_db() as conn:
            conn.execute("UPDATE users SET verified = 1 WHERE device_id = ?", (self.device_id,))

    def reset(self):
        """Consume the verification — the next generation needs a new one."""
        with get_db() as conn:
            conn.execute("""
                UPDATE users SET verified = 0, joined_channels = 0, share_progress = 0,
                last_share_at = NULL WHERE device_id = ?
            """, (self.device_id,))
