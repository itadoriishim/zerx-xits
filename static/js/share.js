/* ============================================
   ZERX XIT - Sharing helper
   Opens WhatsApp reliably across WhatsApp, WhatsApp Business and browsers
   that block custom URL schemes.
   ============================================ */

function isMobileDevice() {
    return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
}

/**
 * Share text through the system share sheet when available (this lets the
 * user pick any installed WhatsApp), otherwise open WhatsApp directly.
 * Always copies the text so it can be pasted if nothing opens.
 * Resolves to 'native' | 'whatsapp' | 'copied'.
 */
async function shareText(text) {
    copyQuietly(text);

    if (navigator.share) {
        try {
            await navigator.share({ text: text });
            return 'native';
        } catch (err) {
            if (err && err.name === 'AbortError') return 'cancelled';
            // fall through to the WhatsApp link
        }
    }

    return openWhatsApp(text);
}

/**
 * Open WhatsApp with a prefilled message.
 * `https://wa.me/?text=` is the officially supported link and is handled by
 * WhatsApp, WhatsApp Business and the web client, so it is used first.
 */
function openWhatsApp(text, phone) {
    const encoded = encodeURIComponent(text || '');
    const base = phone ? `https://wa.me/${String(phone).replace(/\D/g, '')}` : 'https://wa.me/';
    const url = `${base}?text=${encoded}`;

    const win = window.open(url, '_blank', 'noopener');
    if (!win) {
        // Popup blocked (common inside in-app browsers) — navigate instead.
        window.location.href = url;
    }
    return 'whatsapp';
}

function copyQuietly(text) {
    if (!text) return;
    try {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).catch(() => {});
            return;
        }
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
    } catch (e) { /* clipboard is optional */ }
}
