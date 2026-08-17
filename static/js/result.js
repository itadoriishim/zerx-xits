/* ============================================
   ZERX XIT - Result
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
    loadResult();
    initActions();
});

let currentResult = null;

async function loadResult() {
    const data = await api('/api/result');
    if (data.error) {
        showToast('No result yet — generate your settings first.', 'error');
        setTimeout(() => { window.location.href = '/generator'; }, 1500);
        return;
    }
    currentResult = data.result;
    renderResult(data.result);
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function renderResult(result) {
    const di = result.device_info || {};
    setText('resDevice', [di.brand, di.model].filter(Boolean).join(' ') +
        (di.processor ? ` · ${di.processor}` : ''));
    setText('resStyle', `${result.play_style || 'Balanced'}${result.vip ? ' · VIP' : ''}`);

    if (result.tune) {
        const el = document.getElementById('resTune');
        el.style.display = '';
        el.textContent = `Fine tune ${result.tune > 0 ? '+' : ''}${result.tune}`;
    }
    if (result.generated_at) setText('resTime', formatTime(result.generated_at));
    if (result.zerx_id) setText('resId', result.zerx_id);

    const vals = {
        general: result.general, redDot: result.red_dot, scope2x: result.scope2x,
        scope4x: result.scope4x, sniper: result.sniper, freeLook: result.free_look,
        dpi: result.dpi
    };
    const bars = {
        general: 'General', redDot: 'RedDot', scope2x: '2x', scope4x: '4x',
        sniper: 'Sniper', freeLook: 'FreeLook', dpi: 'Dpi'
    };
    Object.entries(bars).forEach(([key, suffix]) => {
        const value = vals[key];
        setText(`val${suffix}`, value == null ? '—' : value);
        const bar = document.getElementById(`bar${suffix}`);
        if (!bar || value == null) return;
        bar.style.width = key === 'dpi'
            ? Math.min(100, (value / 1200) * 100) + '%'
            : Math.min(100, value) + '%';
    });

    animateScore(result.optimization_score || 75);

    const notes = document.getElementById('resNotes');
    if (notes) {
        notes.innerHTML = '';
        (result.notes || []).forEach(note => {
            const li = document.createElement('li');
            li.textContent = note;
            notes.appendChild(li);
        });
    }

    const ai = result.ai_data || {};
    renderTips('tipsPhone', ai.phone_settings);
    renderTips('tipsDev', ai.developer_options);
    renderTips('tipsGaming', ai.gaming_tips);
    renderTips('tipsOpt', ai.optimization_tips);
    renderTips('tipsBattery', ai.battery_tips);
    renderTips('tipsPerf', ai.performance_tips);
    renderTips('tipsSens', ai.sensitivity_advice);

    if (result.vip && ai.advanced && ai.advanced.length) {
        document.getElementById('vipExtra').style.display = 'block';
        renderTips('vipTipsGrid', ai.advanced);
    }
}

function formatTime(value) {
    const date = new Date(String(value).replace(' ', 'T') + (String(value).endsWith('Z') ? '' : 'Z'));
    if (isNaN(date.getTime())) return String(value);
    return date.toLocaleString();
}

function renderTips(id, tips) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    if (!tips || !tips.length) {
        el.innerHTML = '<li class="tip-empty">No items for this device.</li>';
        return;
    }
    tips.forEach(tip => {
        const li = document.createElement('li');
        li.textContent = tip;
        el.appendChild(li);
    });
}

function animateScore(target) {
    const circle = document.getElementById('scoreCircle');
    const num = document.getElementById('scoreNum');
    if (!circle || !num) return;
    const circumference = 2 * Math.PI * 50;
    circle.style.strokeDasharray = circumference;
    circle.style.strokeDashoffset = circumference;

    let current = 0;
    const interval = setInterval(() => {
        current += 2;
        if (current >= target) { current = target; clearInterval(interval); }
        num.textContent = current;
        circle.style.strokeDashoffset = circumference - (current / 100) * circumference;
    }, 20);
}

function resultAsText() {
    const di = currentResult.device_info || {};
    return [
        'ZERX XIT — Free Fire sensitivity',
        `Device: ${[di.brand, di.model].filter(Boolean).join(' ')}`,
        `Play style: ${currentResult.play_style}`,
        '',
        `General: ${currentResult.general}`,
        `Red dot: ${currentResult.red_dot}`,
        `2x scope: ${currentResult.scope2x}`,
        `4x scope: ${currentResult.scope4x}`,
        `Sniper: ${currentResult.sniper}`,
        `Free look: ${currentResult.free_look}`,
        `DPI: ${currentResult.dpi}`,
        '',
        `Generate yours: ${window.location.origin}/generator`
    ].join('\n');
}

function initActions() {
    document.getElementById('btnCopy')?.addEventListener('click', () => {
        if (!currentResult) return;
        copyText(resultAsText());
    });

    document.getElementById('btnShare')?.addEventListener('click', async () => {
        if (!currentResult) return;
        const outcome = await shareText(resultAsText());
        if (outcome === 'copied') showToast('Copied — paste it in any chat', 'success');
    });
}
