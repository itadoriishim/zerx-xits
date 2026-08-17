# ZERX XIT

Free Fire sensitivity generator and device optimization platform.

## Running locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

The app runs on http://localhost:5000 and creates `database.db` on first start.

```bash
.venv/bin/python smoke_test.py   # end-to-end API check
```

## Configuration

Everything has a working default; set these in production (Render → Environment):

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session signing key. Generated and stored on disk if unset. |
| `ADMIN_USERNAME` | Admin dashboard username. |
| `ADMIN_PASSWORD` | Admin dashboard password. |
| `ADMIN_PASSWORD_HASH` | Werkzeug password hash — takes priority over `ADMIN_PASSWORD`. |
| `GEMINI_API_KEY` | Optional. Enables extra written guidance in results. |
| `GEMINI_MODEL` | Optional. Defaults to `gemini-1.5-flash`. |

Generate a password hash:

```bash
.venv/bin/python -c "from werkzeug.security import generate_password_hash as g; print(g('your-password'))"
```

## How generation works

Sensitivity values come from the local engine in `engine.py`. It scores the device from its
processor, GPU, RAM, refresh rate and screen size, then applies the play style multiplier, the
fine-tuning step and a screen calibration factor. **No external API is required** — Gemini, when
configured, only adds written optimization advice and never blocks or changes the values.

## Access model

- **Free** — the join / share / code verification must be completed before *every* generation.
  Progress is stored server-side per device, so it cannot be bypassed from the browser.
- **VIP** — pays the listed amount, uploads a receipt, and the admin approves the request from the
  dashboard. VIP skips verification and unlocks the XIT features.

XIT preferences and device guides are enforced server-side (HTTP 403 for non-VIP). The UI stays
visible to everyone.

## Honest scope

A website cannot change Android system settings. XIT features store your optimization profile and
give you the exact manual steps for your device; they never claim to flip system toggles for you.
Exact device model detection only works in Chromium browsers on Android — everywhere else, use the
device search.
