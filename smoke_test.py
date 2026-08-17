"""Quick smoke test of the key API flows."""
import io
import time

import config
from app import app
from database import get_settings
from verification import MIN_SECONDS_BETWEEN_SHARES

c = app.test_client()


def check(name, cond, extra=''):
    print(('PASS' if cond else 'FAIL'), name, extra)
    assert cond, name


def complete_verification(client):
    """Run the full server-side join / share / code flow."""
    r = client.post('/api/verify/join')
    assert r.status_code == 200, r.get_json()
    required = r.get_json()['status']['required_shares']
    for _ in range(required):
        time.sleep(MIN_SECONDS_BETWEEN_SHARES + 0.2)
        r = client.post('/api/verify/share')
        assert r.status_code == 200, r.get_json()
    return client.post('/api/verify', json={'code': get_settings().get('verification_code')})


for page in ['/', '/generator', '/verify', '/community', '/vip', '/xit', '/admin-login']:
    check(f'page {page}', c.get(page).status_code == 200)

r = c.get('/api/settings')
s = r.get_json()
check('settings', r.status_code == 200 and s['payment']['accounts'][0]['number'])

r = c.get('/api/device/search?q=redmi')
check('device search', r.status_code == 200 and isinstance(r.get_json()['devices'], list),
      str(len(r.get_json()['devices'])))

r = c.get('/api/share-message')
check('share message', r.status_code == 200 and 'whatsapp' in r.get_json()['message'].lower())

# code cannot be submitted before the join/share steps
r = c.post('/api/verify', json={'code': get_settings().get('verification_code')})
check('code blocked before steps', r.status_code == 400, str(r.get_json().get('message')))

r = complete_verification(c)
check('verify correct code', r.status_code == 200 and r.get_json().get('success'), str(r.get_json()))

r = c.post('/api/generate', json={
    'option': 'this', 'play_style': 'Balanced', 'tune': 1,
    'screen': {'width': 1080, 'height': 2400, 'pixel_ratio': 2},
    'detected': {'os': 'Android', 'model': 'Test'}
})
check('generate', r.status_code == 200 and r.get_json().get('success'), str(r.get_json())[:200])
balanced = r.get_json()['result']

r = c.get('/api/result')
check('result', r.status_code == 200 and r.get_json()['result'].get('generated_at'))

# verification is consumed -> next generation is blocked again
r = c.post('/api/generate', json={'option': 'this', 'play_style': 'Balanced', 'detected': {}})
check('re-verify required', r.status_code == 403, str(r.status_code))

# play style changes the values
r = complete_verification(c)
assert r.get_json().get('success')
r = c.post('/api/generate', json={'option': 'this', 'play_style': 'Sniper',
                                  'detected': {'os': 'Android', 'model': 'Test'}})
sniper = r.get_json()['result']
check('play style changes values', sniper['general'] != balanced['general'],
      f"{balanced['general']} vs {sniper['general']}")

# VIP request with a receipt upload
r = c.post('/api/vip/request', data={
    'sender_name': 'Test User',
    'reference': 'TX123',
    'receipt': (io.BytesIO(b'\x89PNG\r\n\x1a\nreceipt'), 'receipt.png', 'image/png')
}, content_type='multipart/form-data')
check('vip request with receipt', r.status_code == 200 and r.get_json()['has_receipt'], str(r.get_json()))

r = c.post('/api/vip/request', data={
    'sender_name': 'Test User',
    'receipt': (io.BytesIO(b'MZ'), 'bad.exe', 'application/x-msdownload')
}, content_type='multipart/form-data')
check('receipt type rejected', r.status_code == 400)

r = c.get('/api/vip/status')
check('vip status pending', r.get_json()['status'] == 'pending')
check('receipt not exposed to user', 'receipt_data' not in r.get_json())

r = c.post('/api/xit/prefs', json={'xit_boost': 1})
check('xit prefs blocked for non-vip', r.status_code == 403 and r.get_json().get('vip_required'))

r = c.post('/api/xit/guide', json={'feature': 'xit_boost'})
check('xit guide blocked for non-vip', r.status_code == 403)

# the admin uses its own session so the user session stays intact
admin = app.test_client()
r = admin.post('/api/admin/login', json={'username': config.ADMIN_USERNAME,
                                         'password': config.ADMIN_PASSWORD})
check('admin login', r.status_code == 200 and r.get_json().get('success'), str(r.get_json()))

r = app.test_client().post('/api/admin/login',
                           json={'username': config.ADMIN_USERNAME, 'password': 'wrong'})
check('admin rejects wrong password', r.status_code == 401)

r = admin.get('/api/admin/vip-requests?status=pending')
reqs = r.get_json()['requests']
check('admin lists vip requests', len(reqs) >= 1)
check('list omits receipt payload', 'receipt_data' not in reqs[0] and reqs[0]['has_receipt'])

rid = reqs[0]['id']
r = admin.get(f'/api/admin/vip-requests/{rid}/receipt')
check('admin can view receipt', r.status_code == 200 and r.mimetype == 'image/png')

r = admin.post(f'/api/admin/vip-requests/{rid}/approve')
check('admin approve', r.status_code == 200 and r.get_json().get('success'))

r = c.get('/api/vip/status')
check('user now vip', r.get_json().get('vip') is True, str(r.get_json()))

r = c.post('/api/xit/prefs', json={'xit_boost': 1})
check('xit prefs allowed for vip', r.status_code == 200)

r = c.post('/api/xit/guide', json={'feature': 'xit_boost'})
check('xit guide allowed for vip', r.status_code == 200 and r.get_json()['steps'])

r = c.post('/api/generate', json={'option': 'this', 'play_style': 'Rusher', 'detected': {}})
check('vip generates without verify', r.status_code == 200, str(r.get_json())[:150])

# an anonymous client must not see the receipt
anon = app.test_client()
check('receipt requires admin', anon.get(f'/api/admin/vip-requests/{rid}/receipt').status_code in (401, 403))

print('ALL PASS')
