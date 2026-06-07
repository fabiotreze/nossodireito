/* NossoDireito v1.43.39 — Termos de Uso/Privacidade banner + Exit toast
 * Não-bloqueante. Estado 100% local (localStorage). Nada enviado a servidor.
 * LGPD-safe: sem PII; auditvel em /historico-aceite.html.
 * CSP-friendly: arquivo externo, sem inline script.
 *
 * TOS_VERSION abaixo é SINCRONIZADA com package.json#version e validada por
 * scripts/check_version_sync.mjs. Bumpar essa string força re-aceite a TODOS
 * os usuários. Bumpe SEMPRE que o texto dos Termos for materialmente alterado
 * (nome do controlador, finalidades, base legal, retencão etc.). Bumps por
 * fix puramente técnico também são aceitáveis pois mantêm a UI consistente
 * com o cabecçalho "Termos atualizados (v...)" do banner.
 */
(function () {
    'use strict';

    var TOS_VERSION = '1.43.39';
    var KEY_VERSION = 'tos_version_accepted';
    var KEY_AT = 'tos_accepted_at';
    var KEY_HASH = 'tos_hash';
    var SAME_HOST = (function () {
        try { return window.location.hostname || ''; } catch (e) { return ''; }
    })();

    function safeGet(key) {
        try { return localStorage.getItem(key); } catch (e) { return null; }
    }
    function safeSet(key, val) {
        try { localStorage.setItem(key, val); return true; } catch (e) { return false; }
    }

    async function sha256Hex(text) {
        try {
            if (window.crypto && window.crypto.subtle && window.TextEncoder) {
                var buf = new TextEncoder().encode(text);
                var hashBuf = await window.crypto.subtle.digest('SHA-256', buf);
                return Array.from(new Uint8Array(hashBuf))
                    .map(function (b) { return b.toString(16).padStart(2, '0'); })
                    .join('');
            }
        } catch (e) { /* fallback abaixo */ }
        return 'unavailable';
    }

    function showBanner() {
        var el = document.getElementById('tosAcceptBanner');
        if (!el) return;
        el.classList.add('tos-show');
        document.body.classList.add('tos-banner-visible');
    }
    function hideBanner() {
        var el = document.getElementById('tosAcceptBanner');
        if (!el) return;
        el.classList.remove('tos-show');
        document.body.classList.remove('tos-banner-visible');
    }

    function needsAcceptance() {
        var saved = safeGet(KEY_VERSION);
        return saved !== TOS_VERSION;
    }

    async function recordAcceptance() {
        var now = new Date().toISOString();
        // Hash representativo: prova qual versão+timestamp foi aceita.
        // Não inclui PII. Auditável em /historico-aceite.html.
        var hash = await sha256Hex('tos:' + TOS_VERSION + '|privacy:' + TOS_VERSION + '|at:' + now);
        safeSet(KEY_VERSION, TOS_VERSION);
        safeSet(KEY_AT, now);
        safeSet(KEY_HASH, hash);
    }

    function initBanner() {
        if (!needsAcceptance()) return;
        var btn = document.getElementById('tosBtnAccept');
        if (btn) {
            btn.addEventListener('click', async function () {
                await recordAcceptance();
                hideBanner();
            });
        }
        showBanner();
    }

    // --- Exit toast para links externos ---
    var toastEl = null;
    var toastTimer = null;
    function showExitToast(hostname) {
        toastEl = toastEl || document.getElementById('externalExitToast');
        if (!toastEl) return;
        // Sanitização defensiva — strings só de URL.hostname são alfanuméricas + .- já.
        var safeHost = String(hostname).replace(/[<>&"']/g, '');
        toastEl.textContent = '';
        var icon = document.createElement('span');
        icon.className = 'exit-toast-icon';
        icon.textContent = '↗ ';
        var prefix = document.createTextNode('Você está saindo do NossoDireito → ');
        var hostStrong = document.createElement('strong');
        hostStrong.textContent = safeHost;
        toastEl.appendChild(icon);
        toastEl.appendChild(prefix);
        toastEl.appendChild(hostStrong);
        toastEl.classList.add('exit-toast-show');
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            if (toastEl) toastEl.classList.remove('exit-toast-show');
        }, 3500);
    }

    function isExternalLink(a) {
        try {
            if (!a.href) return false;
            var u = new URL(a.href, window.location.href);
            if (!/^https?:$/.test(u.protocol)) return false;
            if (!u.hostname) return false;
            if (SAME_HOST && u.hostname === SAME_HOST) return false;
            return true;
        } catch (e) { return false; }
    }

    function initExitToast() {
        document.addEventListener('click', function (e) {
            var node = e.target;
            while (node && node !== document.body && node.nodeName !== 'A') {
                node = node.parentNode;
            }
            if (!node || node.nodeName !== 'A') return;
            if (!isExternalLink(node)) return;
            try {
                var u = new URL(node.href, window.location.href);
                showExitToast(u.hostname);
            } catch (err) { /* ignore */ }
        }, { passive: true });
    }

    function init() {
        initBanner();
        initExitToast();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
