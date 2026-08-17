/* ============================================
   ZERX XIT - XIT features
   Every action is enforced server-side for VIP members.
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
    initXit();
});

const TOGGLES = {
    toggleXitBoost: 'xit_boost',
    toggleTouch: 'touch_optimization',
    toggleFps: 'fps_optimization',
    togglePing: 'low_ping_mode',
    toggleGaming: 'gaming_mode',
    togglePerf: 'performance_mode',
    toggleAim: 'aim_assist_mode',
    toggleLock: 'sensitivity_lock'
};

let xitPrefs = {};
let userProfile = {};
let xitVip = false;

async function initXit() {
    await loadProfile();
    await loadPrefs();
    initToggles();
    initGuides();
    initActions();
    initBattery();
    initNetwork();
    loadXitSettings();
    detectXitDevice();
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

async function detectXitDevice() {
    let model = '';
    try {
        if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
            const hints = await navigator.userAgentData.getHighEntropyValues(['model']);
            model = hints.model || '';
        }
    } catch (e) { /* hint unavailable */ }
    if (!model) {
        const m = navigator.userAgent.match(/Android [\d.]+; ([^;)]+)(?: Build|\))/i);
        if (m && m[1]) model = m[1].trim();
        else if (/iPhone/i.test(navigator.userAgent)) model = 'iPhone';
        else if (/iPad/i.test(navigator.userAgent)) model = 'iPad';
    }
    if (model) {
        setText('wDevice', model);
    } else {
        setText('wDevice', 'Model not reported by this browser');
    }
}

async function loadProfile() {
    const data = await api('/api/profile');
    if (data.error) return;
    userProfile = data.user || {};

    const name = userProfile.brand && userProfile.model
        ? `${userProfile.brand} ${userProfile.model}`
        : 'Player';
    setText('welcomeName', `Welcome, ${name}`);

    const verified = userProfile.verified || userProfile.vip;
    const badge = document.getElementById('statusBadge');
    if (badge) {
        badge.textContent = verified ? 'Verified' : 'Unverified';
        badge.className = 'status-badge ' + (verified ? 'verified' : 'unverified');
    }

    xitVip = !!userProfile.vip;
    if (xitVip) {
        const vipBadge = document.getElementById('vipBadge');
        if (vipBadge) vipBadge.style.display = 'inline-flex';
    } else {
        const banner = document.getElementById('xitLockBanner');
        if (banner) banner.style.display = 'flex';
        document.querySelectorAll('.xit-feature-card').forEach(c => c.classList.add('vip-locked'));
    }

    setText('pZerxId', userProfile.zerx_id || '—');
    setText('pStatus', verified ? 'Verified' : 'Unverified');
    setText('pVip', userProfile.vip ? 'Active' : 'Inactive');
    setText('pGenCount', userProfile.generation_count || 0);

    const list = document.getElementById('recentList');
    if (list && data.recent_generations && data.recent_generations.length) {
        list.innerHTML = '';
        data.recent_generations.forEach(gen => {
            const div = document.createElement('div');
            div.className = 'recent-item';
            div.innerHTML = `
                <div class="recent-info">
                    <strong>${esc(gen.brand || '')} ${esc(gen.model || '')}</strong>
                    <span>${esc(gen.play_style || '')} · ${esc(new Date(gen.generated_at).toLocaleString())}</span>
                </div>`;
            list.appendChild(div);
        });
    }
}

async function loadPrefs() {
    const data = await api('/api/xit/prefs');
    if (data.error) return;
    xitPrefs = data.prefs || {};
    Object.entries(TOGGLES).forEach(([id, key]) => {
        const el = document.getElementById(id);
        if (el) el.checked = !!xitPrefs[key];
    });
}

function requireVip(message) {
    showToast(message, 'error');
    if (typeof openVipModal === 'function') openVipModal();
}

function initToggles() {
    Object.entries(TOGGLES).forEach(([id, key]) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('change', async () => {
            if (!xitVip) {
                el.checked = false;
                requireVip('This feature is available to VIP members.');
                return;
            }
            const res = await api('/api/xit/prefs', {
                method: 'POST',
                body: JSON.stringify({ [key]: el.checked ? 1 : 0 })
            });
            if (res.error) {
                el.checked = !el.checked;
                showToast(res.error, 'error');
                return;
            }
            xitPrefs[key] = el.checked ? 1 : 0;
        });
    });
}

function initGuides() {
    const modal = document.getElementById('guideModal');
    document.getElementById('guideClose')?.addEventListener('click', () => modal.classList.remove('active'));
    modal?.addEventListener('click', (e) => { if (e.target === modal) modal.classList.remove('active'); });

    document.querySelectorAll('.guide-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!xitVip) {
                requireVip('Device guides are available to VIP members.');
                return;
            }
            const res = await api('/api/xit/guide', {
                method: 'POST',
                body: JSON.stringify({ feature: btn.dataset.feature })
            });
            if (res.error) {
                showToast(res.error, 'error');
                return;
            }
            setText('guideTitle', res.title);
            setText('guideDevice', `For ${res.device}`);
            setText('guideNote', res.note);
            const steps = document.getElementById('guideSteps');
            steps.innerHTML = '';
            res.steps.forEach(step => {
                const li = document.createElement('li');
                li.textContent = step;
                steps.appendChild(li);
            });
            modal.classList.add('active');
        });
    });
}

function initActions() {
    document.getElementById('btnSaveConfig')?.addEventListener('click', async () => {
        if (!xitVip) {
            requireVip('Saving an XIT profile is available to VIP members.');
            return;
        }
        const payload = {};
        Object.entries(TOGGLES).forEach(([id, key]) => {
            payload[key] = document.getElementById(id)?.checked ? 1 : 0;
        });
        const res = await api('/api/xit/prefs', { method: 'POST', body: JSON.stringify(payload) });
        showToast(res.error ? res.error : 'Profile saved', res.error ? 'error' : 'success');
    });

    document.getElementById('btnResetConfig')?.addEventListener('click', async () => {
        if (!xitVip) {
            requireVip('Resetting the XIT profile is available to VIP members.');
            return;
        }
        const payload = {};
        Object.entries(TOGGLES).forEach(([id, key]) => {
            payload[key] = 0;
            const el = document.getElementById(id);
            if (el) el.checked = false;
        });
        const res = await api('/api/xit/prefs', { method: 'POST', body: JSON.stringify(payload) });
        showToast(res.error ? res.error : 'Profile reset', res.error ? 'error' : 'success');
    });
}

function initBattery() {
    if (!('getBattery' in navigator)) {
        setText('wBattery', 'Not exposed');
        return;
    }
    navigator.getBattery().then(battery => {
        const render = () => setText('wBattery', Math.round(battery.level * 100) + '%');
        render();
        battery.addEventListener('levelchange', render);
    }).catch(() => setText('wBattery', 'Not exposed'));
}

function initNetwork() {
    const update = () => {
        const el = document.getElementById('wNetwork');
        if (!el) return;
        const conn = navigator.connection;
        const type = conn && conn.effectiveType ? ` · ${conn.effectiveType}` : '';
        el.textContent = (navigator.onLine ? 'Online' : 'Offline') + type;
    };
    update();
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
}

async function loadXitSettings() {
    const data = await api('/api/settings');
    if (data.error) return;
    if (data.mediafire_link) document.getElementById('btnDownload').href = data.mediafire_link;
    if (data.setup_video) document.getElementById('btnSetup').href = data.setup_video;
}
