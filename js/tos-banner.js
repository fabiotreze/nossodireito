/* NossoDireito v1.43.42 — Termos de Uso/Privacidade banner + Exit toast
 * Não-bloqueante. Estado 100% local (localStorage). Nada enviado a servidor.
 * LGPD-safe: sem PII; auditável em /historico-aceite.html.
 * CSP-friendly: arquivo externo, sem inline script.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * TOS_VERSION (formato YYYY-MM-DD) é a data da última MUDANÇA MATERIAL do texto
 * dos Termos de Uso e/ou da Política de Privacidade. É DESACOPLADA de
 * package.json#version desde v1.43.42 (antes: sincronizada — força­va re-aceite
 * a cada bump de site, gerando consent fatigue e treinando o usuário a clicar
 * sem ler, sem ganho jurídico).
 *
 * QUANDO BUMPAR TOS_VERSION (re-aceite obrigatório):
 *   - Mudança de finalidade do tratamento de dados.
 *   - Mudança da base legal (consentimento, legítimo interesse etc.).
 *   - Mudança do controlador / DPO (nome ou contato).
 *   - Mudança de retenção (prazo, política de descarte).
 *   - Mudança de compartilhamento (novo subprocessador, nova transferência
 *     internacional, nova região de processamento).
 *   - Mudança de política de IA (novo provedor, novo modelo com perfil de risco
 *     distinto, nova categoria de dados sensíveis).
 *
 * QUANDO NÃO BUMPAR (re-aceite NÃO é necessário):
 *   - Refactor de CSS/HTML/JS sem mudança de texto material.
 *   - Correções de digitação ou tradução sem mudança de sentido.
 *   - Mudanças de copy ilustrativo (exemplos, ordenação).
 *   - Bumps do site (package.json) por release técnico.
 *
 * Validado por scripts/check_version_sync.mjs (formato + não-futuro).
 * Política completa em GOVERNANCE.md § "Versionamento de Termos".
 * ────────────────────────────────────────────────────────────────────────────
 */
(function () {
    'use strict';

    // YYYY-MM-DD — data da última mudança material do texto dos Termos/Privacidade.
    // Bumpar SOMENTE conforme política em GOVERNANCE.md (NÃO seguir package.json).
    var TOS_VERSION = '2026-06-21';
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
    function safeRemove(key) {
        try { localStorage.removeItem(key); return true; } catch (e) { return false; }
    }

    // Format a TOS_VERSION (YYYY-MM-DD) for UI display: "06/06/2026".
    function formatTosDateBR(iso) {
        if (!iso || typeof iso !== 'string') return iso || '—';
        var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
        if (!m) return iso;
        return m[3] + '/' + m[2] + '/' + m[1];
    }

    function formatDateTimeBR(iso) {
        if (!iso || typeof iso !== 'string') return '—';
        try {
            var d = new Date(iso);
            if (isNaN(d.getTime())) return iso;
            return d.toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch (e) {
            return iso;
        }
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

    var _acceptBtnBound = false;
    function bindAcceptButton() {
        if (_acceptBtnBound) return;
        var btn = document.getElementById('tosBtnAccept');
        if (!btn) return;
        btn.addEventListener('click', async function () {
            await recordAcceptance();
            hideBanner();
            try { document.dispatchEvent(new CustomEvent('tos-acceptance-changed')); } catch (e) { /* ignore */ }
            setupTosConsentManagerRender();
        });
        _acceptBtnBound = true;
    }

    function initBanner() {
        bindAcceptButton();
        if (!needsAcceptance()) return;
        showBanner();
    }

    // v1.43.42 — Painél permanente de gestão de aceite (simétrico ao #aiConsentManager).
    // Mostra versão aceita + botão de revogar (apaga as 3 chaves → banner reaparece na próxima navegação).
    // Exposto via window.revokeTosAcceptance() para reuso (ex.: /historico-aceite.html).
    var _renderTos = null;
    function setupTosConsentManagerRender() {
        if (_renderTos) { _renderTos(); return; }
        var btn = document.getElementById('tosConsentRevokeInline');
        var status = document.getElementById('tosConsentStatus');
        if (!btn || !status) return;
        var animate = function () {
            status.classList.remove('ai-consent-status-badge--updated');
            void status.offsetWidth;
            status.classList.add('ai-consent-status-badge--updated');
            setTimeout(function () { status.classList.remove('ai-consent-status-badge--updated'); }, 260);
        };
        _renderTos = function () {
            var saved = safeGet(KEY_VERSION);
            var acceptedAt = safeGet(KEY_AT);
            status.classList.remove('ai-consent-status-badge--active', 'ai-consent-status-badge--inactive');
            if (saved) {
                var current = (saved === TOS_VERSION);
                status.textContent = current
                    ? ('Aceite ativo (v' + formatTosDateBR(saved) + ') · registrado em ' + formatDateTimeBR(acceptedAt))
                    : ('Aceite antigo (v' + formatTosDateBR(saved) + ') · atual v' + formatTosDateBR(TOS_VERSION));
                status.classList.add('ai-consent-status-badge--active');
                btn.disabled = false;
                btn.textContent = '🔓 Apagar aceite (forçar novo banner)';
            } else {
                status.textContent = 'Não aceito ainda';
                status.classList.add('ai-consent-status-badge--inactive');
                btn.disabled = true;
                btn.textContent = '🔒 Nenhum aceite registrado';
            }
            animate();
        };
        btn.addEventListener('click', function () {
            var ok = window.revokeTosAcceptance && window.revokeTosAcceptance();
            _renderTos();
            if (ok) {
                showBanner();
            }
        });
        document.addEventListener('tos-acceptance-changed', _renderTos);
        _renderTos();
    }

    window.revokeTosAcceptance = function () {
        var hadAny = !!(safeGet(KEY_VERSION) || safeGet(KEY_AT) || safeGet(KEY_HASH));
        if (!hadAny) {
            return false;
        }
        var r1 = safeRemove(KEY_VERSION);
        var r2 = safeRemove(KEY_AT);
        var r3 = safeRemove(KEY_HASH);
        var ok = r1 && r2 && r3;
        try { document.dispatchEvent(new CustomEvent('tos-acceptance-changed')); } catch (e) { /* ignore */ }
        return ok;
    };

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
        setupTosConsentManagerRender();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
