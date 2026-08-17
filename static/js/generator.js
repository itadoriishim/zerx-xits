/* ============================================
   ZERX XIT - Generator
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
    initGenerator();
});

const PENDING_KEY = 'zerx_pending_generation';

let selectedOption = 'this';
let selectedStyle = 'Balanced';
let selectedBrand = '';
let selectedModel = '';
let selectedTune = 0;
let deviceSpecs = null;
let detectedData = {};
let isVip = false;

async function initGenerator() {
    initTabs();
    initStyleChips();
    initTune();
    initDeviceSearch();
    initGenerate();
    loadBrands();
    await detectDevice();
    await checkVipStatus();
    resumePendingGeneration();
}

/* ─── Device detection ──────────────────────────────────────── */
async function detectDevice() {
    const nav = navigator;

    detectedData = {
        os: getOS(),
        browser: getBrowser(),
        platform: nav.platform || 'Unknown',
        screenWidth: window.screen.width,
        screenHeight: window.screen.height,
        pixelRatio: window.devicePixelRatio || 1,
        touchSupport: 'ontouchstart' in window || nav.maxTouchPoints > 0,
        memory: nav.deviceMemory ? nav.deviceMemory + 'GB' : 'Not exposed',
        cpuThreads: nav.hardwareConcurrency || 'Not exposed',
        language: nav.language || 'en',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        userAgent: nav.userAgent,
        gpu: getGPUInfo()
    };

    const model = await getDeviceModel();
    detectedData.model = model || 'Unknown';
    detectedData.brand = guessBrand(model || nav.userAgent);

    setText('dModel', model || `${detectedData.os} device (model not exposed)`);
    setText('dOs', detectedData.os);
    setText('dBrowser', detectedData.browser);
    setText('dScreen', `${detectedData.screenWidth} × ${detectedData.screenHeight}`);
    setText('dPixel', detectedData.pixelRatio + 'x');
    setText('dTouch', detectedData.touchSupport ? 'Yes' : 'No');
    setText('dMemory', detectedData.memory);
    setText('dCpu', detectedData.cpuThreads);
    setText('dGpu', detectedData.gpu);

    if (model) await matchDetectedDevice(model);
}

/** Look the detected model up in the supported-device database. */
async function matchDetectedDevice(model) {
    const data = await api(`/api/device/search?q=${encodeURIComponent(model)}`);
    const status = document.getElementById('matchStatus');
    if (data.error || !data.devices || !data.devices.length) {
        if (status) {
            status.className = 'match-status warn';
            status.textContent = 'This exact model is not in our database yet — settings are calculated from the hardware details above. You can also pick the closest model under "Search device".';
        }
        return;
    }
    const match = data.devices[0];
    detectedData.brand = match.brand;
    detectedData.model = match.model;
    detectedData.processor = match.processor;
    detectedData.gpu = match.gpu;
    detectedData.ram = match.ram;
    detectedData.refresh_rate = match.refresh_rate;
    detectedData.performance_score = match.performance_score;
    detectedData.gaming_score = match.gaming_score;
    if (status) {
        status.className = 'match-status ok';
        status.textContent = `Matched to ${match.brand} ${match.model} — ${match.processor}, ${match.ram}, ${match.refresh_rate}.`;
    }
}

function getOS() {
    const ua = navigator.userAgent;
    if (/Android/i.test(ua)) return 'Android';
    if (/iPhone|iPad|iPod/i.test(ua)) return 'iOS';
    if (/Windows/i.test(ua)) return 'Windows';
    if (/Mac/i.test(ua)) return 'macOS';
    if (/Linux/i.test(ua)) return 'Linux';
    return 'Unknown';
}

function getBrowser() {
    const ua = navigator.userAgent;
    if (/Edg/i.test(ua)) return 'Edge';
    if (/SamsungBrowser/i.test(ua)) return 'Samsung Internet';
    if (/OPR|Opera/i.test(ua)) return 'Opera';
    if (/Chrome/i.test(ua)) return 'Chrome';
    if (/Firefox/i.test(ua)) return 'Firefox';
    if (/Safari/i.test(ua)) return 'Safari';
    return 'Unknown';
}

async function getDeviceModel() {
    // Chromium exposes the real marketing/model name through client hints.
    try {
        if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
            const hints = await navigator.userAgentData.getHighEntropyValues(['model']);
            if (hints.model) return hints.model;
        }
    } catch (e) { /* hint unavailable */ }

    const m = navigator.userAgent.match(/Android [\d.]+; ([^;)]+)(?: Build|\))/i);
    if (m && m[1] && !/^[a-z]{2}(-[a-z]{2})?$/i.test(m[1].trim())) return m[1].trim();
    if (/iPhone/i.test(navigator.userAgent)) return 'iPhone';
    if (/iPad/i.test(navigator.userAgent)) return 'iPad';
    return '';
}

function guessBrand(text) {
    const brands = ['Samsung', 'Redmi', 'POCO', 'Xiaomi', 'Infinix', 'Tecno', 'Itel',
        'Oppo', 'Vivo', 'Realme', 'OnePlus', 'Huawei', 'Honor', 'Nokia', 'Motorola',
        'Google', 'Pixel', 'iPhone', 'Apple'];
    for (const b of brands) {
        if (new RegExp(b, 'i').test(text)) {
            if (b === 'Pixel') return 'Google';
            if (b === 'iPhone') return 'Apple';
            return b;
        }
    }
    return 'Unknown';
}

function getGPUInfo() {
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (!gl) return 'Not exposed';
        const info = gl.getExtension('WEBGL_debug_renderer_info');
        if (info) return gl.getParameter(info.UNMASKED_RENDERER_WEBGL) || 'Not exposed';
    } catch (e) { /* WebGL blocked */ }
    return 'Not exposed';
}

/* ─── Device catalogue ──────────────────────────────────────── */
async function loadBrands() {
    const data = await api('/api/device/brands');
    const select = document.getElementById('brandSelect');
    if (data.error || !select) return;

    data.brands.forEach(brand => {
        const opt = document.createElement('option');
        opt.value = brand;
        opt.textContent = brand;
        select.appendChild(opt);
    });

    select.addEventListener('change', async () => {
        selectedBrand = select.value;
        const modelStep = document.getElementById('modelStep');
        if (!selectedBrand) {
            modelStep.style.display = 'none';
            hideSpecs();
            return;
        }
        const modelsData = await api(`/api/device/models?brand=${encodeURIComponent(selectedBrand)}`);
        const modelSelect = document.getElementById('modelSelect');
        modelSelect.innerHTML = '<option value="">Select model…</option>';
        (modelsData.models || []).forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            modelSelect.appendChild(opt);
        });
        modelStep.style.display = 'block';
    });

    document.getElementById('modelSelect')?.addEventListener('change', async () => {
        selectedModel = document.getElementById('modelSelect').value;
        if (!selectedModel) { hideSpecs(); return; }
        await loadDeviceDetails(selectedBrand, selectedModel);
    });
}

function initDeviceSearch() {
    const input = document.getElementById('deviceSearchInput');
    const results = document.getElementById('deviceSearchResults');
    if (!input || !results) return;

    let timer = null;
    input.addEventListener('input', () => {
        clearTimeout(timer);
        const q = input.value.trim();
        if (q.length < 2) { results.innerHTML = ''; results.classList.remove('open'); return; }
        timer = setTimeout(async () => {
            const data = await api(`/api/device/search?q=${encodeURIComponent(q)}`);
            if (data.error) return;
            results.innerHTML = '';
            if (!data.devices.length) {
                results.innerHTML = '<div class="search-empty">No match. Pick the closest model by brand below.</div>';
                results.classList.add('open');
                return;
            }
            data.devices.forEach(d => {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'search-item';
                item.innerHTML = `<strong>${esc(d.brand)} ${esc(d.model)}</strong><span>${esc(d.processor || '')} · ${esc(d.ram || '')}</span>`;
                item.addEventListener('click', async () => {
                    input.value = `${d.brand} ${d.model}`;
                    results.classList.remove('open');
                    selectedBrand = d.brand;
                    selectedModel = d.model;
                    await loadDeviceDetails(d.brand, d.model);
                });
                results.appendChild(item);
            });
            results.classList.add('open');
        }, 250);
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.device-search')) results.classList.remove('open');
    });
}

async function loadDeviceDetails(brand, model) {
    const details = await api(`/api/device/details?brand=${encodeURIComponent(brand)}&model=${encodeURIComponent(model)}`);
    if (details.error) { hideSpecs(); return; }
    deviceSpecs = details;
    setText('sProc', details.processor || 'Unknown');
    setText('sGpu', details.gpu || 'Unknown');
    setText('sRam', details.ram || 'Unknown');
    setText('sAndroid', details.android_version || 'Unknown');
    setText('sRefresh', details.refresh_rate || 'Unknown');
    setText('sArch', details.architecture || 'Unknown');
    document.getElementById('deviceSpecs').style.display = 'block';
}

function hideSpecs() {
    deviceSpecs = null;
    const el = document.getElementById('deviceSpecs');
    if (el) el.style.display = 'none';
}

/* ─── Options, style, fine tuning ───────────────────────────── */
function initTabs() {
    document.querySelectorAll('.option-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.option-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            selectedOption = tab.dataset.option;
            document.querySelectorAll('.option-panel').forEach(p => p.classList.remove('active'));
            document.getElementById(selectedOption === 'this' ? 'panelThis' : 'panelOther').classList.add('active');
        });
    });
}

const STYLE_HINTS = {
    'One Tap': 'Lower sensitivity for precise headshots.',
    'Balanced': 'Well-rounded values for every situation.',
    'Rusher': 'Faster turning for close-range fights.',
    'Freestyle': 'Smooth transitions between movement and aim.',
    'Sniper': 'Slow, stable tracking for long range.',
    'Instaplayer': 'Maximum speed — for experienced players.'
};

function initStyleChips() {
    document.querySelectorAll('.style-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.style-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            selectedStyle = chip.dataset.style;
            setText('styleHint', STYLE_HINTS[selectedStyle] || selectedStyle);
        });
    });
}

function initTune() {
    document.querySelectorAll('.tune-option').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tune-option').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedTune = parseInt(btn.dataset.tune, 10) || 0;
        });
    });
}

/* ─── VIP ───────────────────────────────────────────────────── */
async function checkVipStatus() {
    const data = await api('/api/check-verification');
    const banner = document.getElementById('vipBanner');
    const btn = document.getElementById('vipToggleBtn');
    if (data.vip) {
        isVip = true;
        banner?.classList.add('vip-active');
        if (btn) { btn.textContent = 'VIP ACTIVE'; btn.disabled = true; }
        setText('generateNote', 'VIP active — generate as many profiles as you need, no verification.');
    } else {
        btn?.addEventListener('click', () => openVipModal());
    }
}

/* ─── Generation ────────────────────────────────────────────── */
function buildPayload() {
    const payload = {
        option: selectedOption,
        play_style: selectedStyle,
        tune: selectedTune,
        screen: {
            width: window.screen.width,
            height: window.screen.height,
            pixel_ratio: window.devicePixelRatio || 1
        }
    };

    if (selectedOption === 'this') {
        payload.detected = detectedData;
    } else {
        if (!selectedBrand || !selectedModel) return null;
        payload.brand = selectedBrand;
        payload.model = selectedModel;
        if (deviceSpecs) {
            payload.processor = deviceSpecs.processor;
            payload.gpu = deviceSpecs.gpu;
            payload.ram = deviceSpecs.ram;
            payload.android_version = deviceSpecs.android_version;
            payload.refresh_rate = deviceSpecs.refresh_rate;
        }
    }
    return payload;
}

function initGenerate() {
    document.getElementById('generateBtn')?.addEventListener('click', () => {
        const payload = buildPayload();
        if (!payload) {
            showToast('Search or select a device first', 'error');
            document.querySelector('.option-tab[data-option="other"]')?.click();
            return;
        }
        runGeneration(payload);
    });
}

async function runGeneration(payload) {
    const btn = document.getElementById('generateBtn');
    if (btn) btn.disabled = true;
    showLoading();

    const res = await api('/api/generate', { method: 'POST', body: JSON.stringify(payload) });

    hideLoading();
    if (btn) btn.disabled = false;

    if (res.success) {
        sessionStorage.removeItem(PENDING_KEY);
        window.location.href = '/result';
        return;
    }

    if (res.status === 403 && /verification/i.test(res.error || '')) {
        sessionStorage.setItem(PENDING_KEY, JSON.stringify(payload));
        showToast('Verification required before each free generation.', 'info');
        setTimeout(() => { window.location.href = '/verify'; }, 900);
        return;
    }
    if (res.banned || res.status === 403) {
        window.location.href = '/banned';
        return;
    }
    showToast(res.error || 'Generation failed. Please try again.', 'error');
}

/** After verifying, continue the generation the user already configured. */
function resumePendingGeneration() {
    const params = new URLSearchParams(window.location.search);
    const stored = sessionStorage.getItem(PENDING_KEY);
    if (!params.get('resume') || !stored) return;
    try {
        runGeneration(JSON.parse(stored));
    } catch (e) {
        sessionStorage.removeItem(PENDING_KEY);
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}
