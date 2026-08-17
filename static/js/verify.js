/* ============================================
   ZERX XIT - Verification
   Progress is tracked server-side; this file only drives the UI.
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
    initVerification();
});

let verifyState = { joined: false, shares: 0, required_shares: 5, shares_complete: false };
let shareMessage = '';

async function initVerification() {
    await loadVerifySettings();
    await refreshVerifyState();
    initJoin();
    initShare();
    initVerifyCode();
}

async function loadVerifySettings() {
    const data = await api('/api/settings');
    if (!data.error) {
        if (data.whatsapp_channel) document.getElementById('btnWhatsapp').href = data.whatsapp_channel;
        if (data.telegram_main) document.getElementById('btnTelegram').href = data.telegram_main;
    }
    const msgData = await api('/api/share-message');
    if (!msgData.error) shareMessage = msgData.message;
}

async function refreshVerifyState() {
    const status = await api('/api/verify/status');
    if (status.error) return;
    verifyState = status;
    renderVerifyState();
}

function renderVerifyState() {
    const required = verifyState.required_shares || 5;
    setText('shareCount', required);
    setText('shareCounter', `${verifyState.shares} / ${required}`);

    const joinBtn = document.getElementById('markJoined');
    if (joinBtn && verifyState.joined) {
        joinBtn.disabled = true;
        joinBtn.innerHTML = '<span class="btn-icon">✓</span> JOINED';
    }

    setStepLocked(2, !verifyState.joined);
    setStepLocked(3, !verifyState.shares_complete);
    document.getElementById('shareCounter')?.classList.toggle('complete', !!verifyState.shares_complete);

    let completed = 0;
    if (verifyState.joined) completed++;
    if (verifyState.shares_complete) completed++;
    const progress = document.getElementById('verifyProgress');
    if (progress) progress.style.width = `${(completed / 3) * 100}%`;
    document.querySelectorAll('.pstep').forEach((step, i) => {
        step.classList.toggle('done', i < completed);
        step.classList.toggle('active', i === completed);
    });
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function setStepLocked(step, locked) {
    document.querySelector(`.step-card[data-step="${step}"]`)?.classList.toggle('locked', locked);
}

function initJoin() {
    const btn = document.getElementById('markJoined');
    if (!btn) return;
    btn.addEventListener('click', async () => {
        btn.disabled = true;
        const res = await api('/api/verify/join', { method: 'POST' });
        if (res.error) {
            btn.disabled = false;
            showToast(res.error, 'error');
            return;
        }
        verifyState = res.status;
        renderVerifyState();
        showToast('Step 1 complete. Now share the invite.', 'success');
    });
}

function initShare() {
    const btn = document.getElementById('btnShare');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        if (!verifyState.joined) {
            showToast('Complete step 1 first', 'error');
            return;
        }
        if (verifyState.shares_complete) {
            showToast('Sharing is complete — enter the code below', 'success');
            return;
        }

        const outcome = await shareText(shareMessage);
        if (outcome === 'cancelled') return;

        const res = await api('/api/verify/share', { method: 'POST' });
        if (res.error) {
            if (res.status) verifyState = res.status;
            renderVerifyState();
            showToast(res.error, 'error');
            return;
        }
        verifyState = res.status;
        renderVerifyState();
        if (verifyState.shares_complete) {
            showToast('Sharing complete. Enter the verification code.', 'success');
        } else {
            showToast(`Share ${verifyState.shares} of ${verifyState.required_shares} counted.`, 'info');
        }
    });
}

function initVerifyCode() {
    const btn = document.getElementById('btnVerify');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        if (!verifyState.shares_complete) {
            showToast('Complete the sharing step first', 'error');
            return;
        }
        const code = document.getElementById('verifyCode').value.trim().toUpperCase();
        if (!code) {
            showToast('Enter the verification code', 'error');
            return;
        }

        btn.disabled = true;
        const res = await api('/api/verify', { method: 'POST', body: JSON.stringify({ code: code }) });
        btn.disabled = false;

        if (res.banned) {
            window.location.href = '/banned';
            return;
        }
        if (res.success) {
            showToast('Verified. Returning to the generator...', 'success');
            const resume = sessionStorage.getItem('zerx_pending_generation') ? '?resume=1' : '';
            setTimeout(() => { window.location.href = '/generator' + resume; }, 900);
            return;
        }
        showToast(res.message || res.error || 'Verification failed', 'error');
    });
}
