/* ============================================
   ZERX XIT - Admin Dashboard JavaScript
   ============================================ */
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initNavigation();
    initLogout();
    loadDashboard();
    initUsers();
    initBans();
    initAppeals();
    initVipRequests();
    initDevices();
    initSettings();
    initAnalytics();
});

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

async function api(endpoint, options = {}) {
    try {
        const res = await fetch(endpoint, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        });
        if (res.status === 401) {
            window.location.href = '/admin-login';
            return { error: 'Unauthorized' };
        }
        return await res.json();
    } catch (err) {
        showToast('Network error', 'error');
        return { error: err.message };
    }
}

async function checkAuth() {
    const data = await api('/api/admin/check');
    if (!data.logged_in) {
        window.location.href = '/admin-login';
    }
}

function initNavigation() {
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            showPage(page);
            document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
    document.getElementById('sidebarToggle')?.addEventListener('click', () => {
        document.getElementById('adminSidebar').classList.toggle('active');
    });
}

function showPage(page) {
    document.querySelectorAll('.admin-page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`)?.classList.add('active');
    document.getElementById('pageTitle').textContent = page.charAt(0).toUpperCase() + page.slice(1);
    if (page === 'users') loadUsers();
    if (page === 'bans') loadBans();
    if (page === 'appeals') loadAppeals();
    if (page === 'vip') loadVipRequests();
    if (page === 'devices') loadDevices();
    if (page === 'settings') loadSettingsData();
    if (page === 'analytics') loadAnalytics();
}

function initLogout() {
    document.getElementById('btnLogout')?.addEventListener('click', async () => {
        await api('/api/admin/logout', { method: 'POST' });
        window.location.href = '/admin-login';
    });
}

async function loadDashboard() {
    const data = await api('/api/admin/dashboard');
    if (data.error) return;
    const s = data.stats;
    document.getElementById('stTotalUsers').textContent = s.total_users || 0;
    document.getElementById('stVerified').textContent = s.verified_users || 0;
    document.getElementById('stVip').textContent = s.vip_users || 0;
    document.getElementById('stGenerations').textContent = s.total_generations || 0;
    document.getElementById('stAppeals').textContent = s.pending_appeals || 0;
    document.getElementById('stBanned').textContent = s.banned_devices || 0;
    document.getElementById('stToday').textContent = s.today_visitors || 0;
    const actList = document.getElementById('dashActivity');
    if (actList && s.recent_activity) {
        actList.innerHTML = s.recent_activity.slice(0, 10).map(a =>
            `<div class="dash-item"><strong>${a.action}</strong> — ${a.details} <span style="color:#666;float:right">${new Date(a.created_at).toLocaleTimeString()}</span></div>`
        ).join('');
    }
    const userList = document.getElementById('dashUsers');
    if (userList && s.recent_users) {
        userList.innerHTML = s.recent_users.slice(0, 10).map(u =>
            `<div class="dash-item">${u.zerx_id} — ${u.brand || 'Unknown'} ${u.model || ''} <span style="color:#666;float:right">${u.verified ? '✓' : '○'}</span></div>`
        ).join('');
    }
    const phoneList = document.getElementById('dashPhones');
    if (phoneList && s.popular_phones) {
        phoneList.innerHTML = s.popular_phones.map(p =>
            `<div class="dash-item">${p.brand} ${p.model} <span style="color:var(--primary);float:right">${p.count}</span></div>`
        ).join('');
    }
    const styleList = document.getElementById('dashStyles');
    if (styleList && s.popular_styles) {
        styleList.innerHTML = s.popular_styles.map(st =>
            `<div class="dash-item">${st.play_style} <span style="color:var(--primary);float:right">${st.count}</span></div>`
        ).join('');
    }
}

function initUsers() {
    document.getElementById('btnSearchUsers')?.addEventListener('click', loadUsers);
    document.getElementById('userSearch')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadUsers();
    });
}

async function loadUsers() {
    const search = document.getElementById('userSearch')?.value || '';
    const data = await api(`/api/admin/users?search=${encodeURIComponent(search)}`);
    if (data.error) return;
    const tbody = document.getElementById('usersTable');
    tbody.innerHTML = data.users.map(u => `
        <tr>
            <td>${u.id}</td>
            <td>${u.zerx_id}</td>
            <td>${u.device_id.substring(0, 20)}...</td>
            <td>${u.brand || '-'} ${u.model || ''}</td>
            <td>${u.verified ? '✅' : '❌'}</td>
            <td>${u.vip ? '👑' : '—'}</td>
            <td>${new Date(u.created_at).toLocaleDateString()}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="toggleUserVip(${u.id}, ${u.vip ? 0 : 1})">${u.vip ? 'Remove VIP' : 'Make VIP'}</button>
                <button class="btn btn-sm btn-outline" onclick="toggleUserVerify(${u.id}, ${u.verified ? 0 : 1})">${u.verified ? 'Unverify' : 'Verify'}</button>
            </td>
        </tr>
    `).join('');
}

async function toggleUserVip(id, vip) {
    await api(`/api/admin/users/${id}/vip`, { method: 'POST', body: JSON.stringify({ vip }) });
    loadUsers();
    showToast('User updated', 'success');
}

async function toggleUserVerify(id, verified) {
    await api(`/api/admin/users/${id}/verify`, { method: 'POST', body: JSON.stringify({ verified }) });
    loadUsers();
    showToast('User updated', 'success');
}

function initBans() {
    document.getElementById('banFilter')?.addEventListener('change', loadBans);
}

async function loadBans() {
    const status = document.getElementById('banFilter')?.value || 'active';
    const data = await api(`/api/admin/bans?status=${status}`);
    if (data.error) return;
    const tbody = document.getElementById('bansTable');
    tbody.innerHTML = data.bans.map(b => `
        <tr>
            <td>${b.zerx_id}</td>
            <td>${b.device_id.substring(0, 20)}...</td>
            <td>${b.reason}</td>
            <td>${new Date(b.created_at).toLocaleDateString()}</td>
            <td>${b.status}</td>
            <td>
                ${b.status === 'active' ? `<button class="btn btn-sm btn-primary" onclick="unbanDevice('${b.device_id}')">Unban</button>` : '—'}
            </td>
        </tr>
    `).join('');
}

async function unbanDevice(deviceId) {
    await api('/api/admin/bans/unban', { method: 'POST', body: JSON.stringify({ device_id: deviceId }) });
    loadBans();
    showToast('Device unbanned', 'success');
}

async function loadAppeals() {
    const data = await api('/api/admin/appeals?status=pending');
    if (data.error) return;
    const tbody = document.getElementById('appealsTable');
    tbody.innerHTML = data.appeals.map(a => `
        <tr>
            <td>${a.zerx_id}</td>
            <td>${a.device_id.substring(0, 20)}...</td>
            <td>${a.message}</td>
            <td>${new Date(a.created_at).toLocaleDateString()}</td>
            <td>${a.status}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="approveAppeal(${a.id})">Approve</button>
                <button class="btn btn-sm btn-outline" onclick="rejectAppeal(${a.id})">Reject</button>
            </td>
        </tr>
    `).join('');
}

async function approveAppeal(id) {
    await api(`/api/admin/appeals/${id}/approve`, { method: 'POST' });
    loadAppeals();
    showToast('Appeal approved', 'success');
}

async function rejectAppeal(id) {
    await api(`/api/admin/appeals/${id}/reject`, { method: 'POST' });
    loadAppeals();
    showToast('Appeal rejected', 'success');
}

function initDevices() {
    document.getElementById('btnAddDevice')?.addEventListener('click', () => {
        const brand = prompt('Brand:');
        const model = prompt('Model:');
        if (brand && model) {
            api('/api/admin/devices', {
                method: 'POST',
                body: JSON.stringify({ brand, model })
            }).then(() => { loadDevices(); showToast('Device added', 'success'); });
        }
    });
}

function escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str == null ? '' : String(str);
    return div.innerHTML;
}

function initVipRequests() {
    document.getElementById('vipFilter')?.addEventListener('change', loadVipRequests);
}

async function loadVipRequests() {
    const status = document.getElementById('vipFilter')?.value ?? 'pending';
    const data = await api(`/api/admin/vip-requests?status=${encodeURIComponent(status)}`);
    if (data.error) return;
    const tbody = document.getElementById('vipTable');
    tbody.innerHTML = '';
    if (!data.requests.length) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-muted)">No VIP requests</td></tr>';
        return;
    }
    data.requests.forEach(r => {
        const tr = document.createElement('tr');
        const actions = r.status === 'pending'
            ? `<button class="btn btn-sm btn-primary" data-approve="${r.id}">Approve</button>
               <button class="btn btn-sm btn-outline" data-reject="${r.id}">Reject</button>`
            : '';
        tr.innerHTML = `
            <td>${r.id}</td>
            <td>${escHtml(r.zerx_id)}</td>
            <td>${escHtml(r.sender_name)}</td>
            <td>${escHtml(r.payment_reference || '—')}</td>
            <td>${r.has_receipt
                ? `<a class="btn btn-sm btn-outline" href="/api/admin/vip-requests/${r.id}/receipt" target="_blank" rel="noopener">View</a>`
                : '—'}</td>
            <td>${escHtml(r.created_at)}</td>
            <td><span class="vip-status-pill ${escHtml(r.status)}">${escHtml(r.status)}</span></td>
            <td>${actions}</td>
        `;
        tbody.appendChild(tr);
    });
    tbody.querySelectorAll('[data-approve]').forEach(b => {
        b.addEventListener('click', async () => {
            const res = await api(`/api/admin/vip-requests/${b.dataset.approve}/approve`, { method: 'POST' });
            if (res.success) { showToast('VIP activated for user', 'success'); loadVipRequests(); }
            else showToast(res.error || 'Failed', 'error');
        });
    });
    tbody.querySelectorAll('[data-reject]').forEach(b => {
        b.addEventListener('click', async () => {
            const res = await api(`/api/admin/vip-requests/${b.dataset.reject}/reject`, { method: 'POST' });
            if (res.success) { showToast('Request rejected', 'success'); loadVipRequests(); }
            else showToast(res.error || 'Failed', 'error');
        });
    });
}

async function loadDevices() {
    const brand = document.getElementById('deviceBrandFilter')?.value || '';
    const data = await api(`/api/admin/devices?brand=${encodeURIComponent(brand)}`);
    if (data.error) return;
    const tbody = document.getElementById('devicesTable');
    tbody.innerHTML = data.devices.map(d => `
        <tr>
            <td>${d.brand}</td>
            <td>${d.model}</td>
            <td>${d.processor || '-'}</td>
            <td>${d.gpu || '-'}</td>
            <td>${d.ram || '-'}</td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="deleteDevice(${d.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

async function deleteDevice(id) {
    if (!confirm('Delete this device?')) return;
    await api(`/api/admin/devices/${id}`, { method: 'DELETE' });
    loadDevices();
    showToast('Device deleted', 'success');
}

function initSettings() {
    document.getElementById('btnSaveSettings')?.addEventListener('click', async () => {
        const payload = {
            verification_code: document.getElementById('setCode')?.value,
            whatsapp_channel: document.getElementById('setWhatsapp')?.value,
            telegram_main: document.getElementById('setTelegram')?.value,
            telegram_backup: document.getElementById('setBackup')?.value,
            share_count: parseInt(document.getElementById('setShares')?.value) || 5,
            mediafire_link: document.getElementById('setMediafire')?.value,
            setup_video: document.getElementById('setVideo')?.value,
            vip_price: document.getElementById('setVipPrice')?.value,
            vip_enabled: document.getElementById('setVipEnabled')?.checked ? 1 : 0,
            premium_ai_enabled: document.getElementById('setPremiumAi')?.checked ? 1 : 0,
            ai_enabled: document.getElementById('setAiEnabled')?.checked ? 1 : 0,
            gemini_model: document.getElementById('setModel')?.value
        };
        await api('/api/admin/settings', { method: 'POST', body: JSON.stringify(payload) });
        showToast('Settings saved!', 'success');
    });
}

async function loadSettingsData() {
    const data = await api('/api/admin/settings');
    if (data.error) return;
    const s = data.settings;
    if (document.getElementById('setCode')) document.getElementById('setCode').value = s.verification_code || '';
    if (document.getElementById('setWhatsapp')) document.getElementById('setWhatsapp').value = s.whatsapp_channel || '';
    if (document.getElementById('setTelegram')) document.getElementById('setTelegram').value = s.telegram_main || '';
    if (document.getElementById('setBackup')) document.getElementById('setBackup').value = s.telegram_backup || '';
    if (document.getElementById('setShares')) document.getElementById('setShares').value = s.share_count || 5;
    if (document.getElementById('setMediafire')) document.getElementById('setMediafire').value = s.mediafire_link || '';
    if (document.getElementById('setVideo')) document.getElementById('setVideo').value = s.setup_video || '';
    if (document.getElementById('setVipPrice')) document.getElementById('setVipPrice').value = s.vip_price || '₦2000';
    if (document.getElementById('setVipEnabled')) document.getElementById('setVipEnabled').checked = s.vip_enabled === 1;
    if (document.getElementById('setPremiumAi')) document.getElementById('setPremiumAi').checked = s.premium_ai_enabled === 1;
    if (document.getElementById('setAiEnabled')) document.getElementById('setAiEnabled').checked = s.ai_enabled === 1;
    if (document.getElementById('setModel')) document.getElementById('setModel').value = s.gemini_model || 'gemini-1.5-flash';
}

function initAnalytics() {}

async function loadAnalytics() {
    const data = await api('/api/admin/analytics');
    if (data.error) return;
    document.getElementById('statVerifyRate').textContent = (data.verification_rate || 0) + '%';
    const aStats = document.getElementById('appealStats');
    if (aStats && data.appeals) {
        aStats.innerHTML = `
            <div class="appeal-stat"><span class="appeal-stat-value">${data.appeals.total}</span><span class="appeal-stat-label">Total</span></div>
            <div class="appeal-stat"><span class="appeal-stat-value">${data.appeals.pending}</span><span class="appeal-stat-label">Pending</span></div>
            <div class="appeal-stat"><span class="appeal-stat-value">${data.appeals.approved}</span><span class="appeal-stat-label">Approved</span></div>
            <div class="appeal-stat"><span class="appeal-stat-value">${data.appeals.rejected}</span><span class="appeal-stat-label">Rejected</span></div>
        `;
    }
    if (data.daily_visitors) {
        document.getElementById('chartVisitors').innerHTML = data.daily_visitors.map(v =>
            `<div style="display:inline-block;width:30px;margin:0 2px;text-align:center">
                <div style="height:${Math.min(150, v.count * 5)}px;background:var(--primary);border-radius:4px 4px 0 0;opacity:0.8"></div>
                <span style="font-size:10px;color:var(--text-muted)">${v.day.slice(5)}</span>
            </div>`
        ).join('');
    }
}
