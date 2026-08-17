/* ============================================
   ZERX XIT - Global JavaScript
   ============================================ */
let siteSettings = null;

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initFAQ();
    loadSettings();
    initVipModal();
});

function esc(str) {
    const div = document.createElement('div');
    div.textContent = str == null ? '' : String(str);
    return div.innerHTML;
}

/* ─── Navigation ────────────────────────────────────────────── */
function initNavigation() {
    const toggle = document.getElementById('navToggle');
    const menu = document.getElementById('navMenu');
    if (toggle && menu) {
        toggle.addEventListener('click', () => {
            const open = menu.classList.toggle('active');
            toggle.classList.toggle('active', open);
            toggle.setAttribute('aria-expanded', String(open));
        });
        menu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                menu.classList.remove('active');
                toggle.classList.remove('active');
                toggle.setAttribute('aria-expanded', 'false');
            });
        });
    }
    const nav = document.getElementById('navbar');
    if (nav) {
        const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 20);
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }
}

function initFAQ() {
    document.querySelectorAll('.faq-question').forEach(btn => {
        btn.addEventListener('click', () => {
            const item = btn.parentElement;
            const isActive = item.classList.contains('active');
            document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));
            if (!isActive) item.classList.add('active');
        });
    });
}

/* ─── Feedback ──────────────────────────────────────────────── */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

function showLoading(text) {
    const overlay = document.getElementById('loadingOverlay');
    if (!overlay) return;
    const label = document.getElementById('loadingText');
    if (label && text) label.textContent = text;
    overlay.classList.add('active');
    overlay.setAttribute('aria-hidden', 'false');
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (!overlay) return;
    overlay.classList.remove('active');
    overlay.setAttribute('aria-hidden', 'true');
}

/* ─── API helper ────────────────────────────────────────────── */
async function api(endpoint, options = {}) {
    const config = { credentials: 'same-origin', ...options };
    const isForm = config.body instanceof FormData;
    config.headers = isForm
        ? { ...(options.headers || {}) }
        : { 'Content-Type': 'application/json', ...(options.headers || {}) };

    try {
        const res = await fetch(endpoint, config);
        let data = null;
        try { data = await res.json(); } catch (e) { /* non-JSON response */ }
        if (!res.ok) {
            const msg = (data && (data.error || data.message)) || `Request failed (${res.status})`;
            return { error: msg, status: res.status, ...(data || {}) };
        }
        return data || {};
    } catch (err) {
        return { error: 'Could not reach the server. Check your connection and try again.', offline: true };
    }
}

function setLink(id, href) {
    const el = document.getElementById(id);
    if (el && href) el.href = href;
}

async function loadSettings() {
    const data = await api('/api/settings');
    if (data.error) return;
    siteSettings = data;

    if (data.vip_price) {
        document.querySelectorAll('#vipPrice, #faqVipPrice, #vipPagePrice').forEach(el => {
            if (el) el.textContent = data.vip_price;
        });
    }

    const adminTg = data.admin_telegram
        ? `https://t.me/${data.admin_telegram.replace('@', '')}`
        : '';

    const links = {
        commWhatsapp: data.whatsapp_channel,
        commWhatsapp2: data.whatsapp_channel_2,
        commTelegram: data.telegram_main,
        commLeaks: data.telegram_leaks || data.telegram_backup,
        commBackup: data.telegram_backup,
        commAdminTg: adminTg,
        commAdminWa: data.admin_whatsapp,
        supportTelegram: adminTg,
        supportWhatsapp: data.admin_whatsapp,
        vipContactWhatsapp: data.admin_whatsapp,
        vipContactTelegram: adminTg,
        footerWhatsapp: data.whatsapp_channel,
        footerTelegram: data.telegram_main,
        footerAdminWa: data.admin_whatsapp,
        footerAdminTg: adminTg
    };
    Object.entries(links).forEach(([id, href]) => setLink(id, href));
}

/* ─── VIP Activation Modal ──────────────────────────────────── */
function initVipModal() {
    const modal = document.getElementById('vipModal');
    if (!modal) return;

    document.getElementById('vipModalClose')?.addEventListener('click', closeVipModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeVipModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeVipModal(); });

    document.querySelectorAll('.vip-activate-btn, #navVip').forEach(btn => {
        btn.addEventListener('click', (e) => { e.preventDefault(); openVipModal(); });
    });

    document.getElementById('vipForm')?.addEventListener('submit', submitVipRequest);
}

async function submitVipRequest(event) {
    event.preventDefault();
    const sender = document.getElementById('vipSenderName').value.trim();
    const reference = document.getElementById('vipReference').value.trim();
    const file = document.getElementById('vipReceipt').files[0];
    const btn = document.getElementById('vipSubmitBtn');

    if (!sender) {
        showToast('Enter the name used to make the payment', 'error');
        return;
    }
    if (file && file.size > 4 * 1024 * 1024) {
        showToast('Receipt is larger than 4MB. Upload a smaller screenshot.', 'error');
        return;
    }

    const form = new FormData();
    form.append('sender_name', sender);
    form.append('reference', reference);
    if (file) form.append('receipt', file);

    btn.disabled = true;
    btn.textContent = 'Submitting…';
    const res = await api('/api/vip/request', { method: 'POST', body: form });
    btn.disabled = false;
    btn.textContent = 'Submit payment for confirmation';

    if (res.error) {
        showToast(res.error, 'error');
        return;
    }
    showToast(res.message || 'Submitted for confirmation', 'success');
    showVipPending();
}

function showVipPending() {
    document.getElementById('vipForm')?.setAttribute('style', 'display:none');
    const pending = document.getElementById('vipPending');
    if (pending) pending.style.display = 'block';
}

async function openVipModal() {
    const modal = document.getElementById('vipModal');
    if (!modal) return;

    if (!siteSettings) await loadSettings();
    const pay = (siteSettings && siteSettings.payment) || { accounts: [] };

    const priceEl = document.getElementById('vipModalPrice');
    if (priceEl && pay.price) priceEl.textContent = pay.price;

    const container = document.getElementById('payAccounts');
    if (container) {
        container.innerHTML = (pay.accounts || []).filter(a => a.number).map(a => `
            <div class="pay-account">
                <div class="pay-bank">${esc(a.bank)}</div>
                <div class="pay-number">
                    <span>${esc(a.number)}</span>
                    <button type="button" class="copy-btn" data-copy="${esc(a.number)}">Copy</button>
                </div>
                <div class="pay-name">${esc(a.name)}</div>
            </div>
        `).join('');
        container.querySelectorAll('.copy-btn').forEach(b => {
            b.addEventListener('click', () => copyText(b.dataset.copy));
        });
    }

    const status = await api('/api/vip/status');
    if (status.vip) {
        showToast('VIP is already active on this device', 'success');
        return;
    }
    if (status.status === 'pending') showVipPending();

    modal.classList.add('active');
}

function closeVipModal() {
    document.getElementById('vipModal')?.classList.remove('active');
}

function copyText(text) {
    const done = () => showToast('Copied', 'success');
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
    } else {
        fallbackCopy(text, done);
    }
}

function fallbackCopy(text, done) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); done(); } catch (e) { showToast('Copy failed', 'error'); }
    document.body.removeChild(ta);
}
