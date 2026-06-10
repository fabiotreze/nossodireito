
(function () {
    'use strict';
    // Swap deferred CSS from media="print" to "all" (avoids inline onload blocked by CSP)
    var _css = document.getElementById('deferredCSS');
    if (_css) _css.media = 'all';
    // Fetch JSON data eagerly at module scope (before DOMContentLoaded).
    // Replaces <link rel="preload"> which had credential-mode mismatch.
    // AbortController prevents ERR_TIMED_OUT on cold starts.
    // 12000ms: App Service B1 cold start can take 8-12s; 6000ms was too tight
    // causing Google Search Console to log XHR failures on cold-start renders.
    function _earlyFetch(url) {
        const c = new AbortController();
        const t = setTimeout(() => c.abort(), 12000);
        return fetch(url, { signal: c.signal }).then(r => { clearTimeout(t); return r.ok ? r : Promise.reject(r); }).catch(() => { clearTimeout(t); return null; });
    }
    const _earlyDireitos = _earlyFetch('data/direitos.json');
    const _earlyMatching = _earlyFetch('data/matching_engine.json');
    const _earlyDicionario = _earlyFetch('data/dicionario_pcd.json');
    const _earlyLegalReview = _earlyFetch('data/revisao_juridica.json');
    // Geo snapshot (IBGE, 5570 municípios, ~80 KB gzipped). Non-blocking on first paint.
    const _earlyMunicipios = _earlyFetch('data/municipios_br.json');
    function safeJsonParse(str) {
        return JSON.parse(str, (key, value) => {
            if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
                return undefined;
            }
            return value;
        });
    }
    function deepFreeze(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        Object.freeze(obj);
        Object.getOwnPropertyNames(obj).forEach(prop => {
            const val = obj[prop];
            if (val !== null && typeof val === 'object' && !Object.isFrozen(val)) {
                deepFreeze(val);
            }
        });
        return obj;
    }
    async function resilientFetch(url, retries = 2, delay = 500) {
        for (let attempt = 0; attempt <= retries; attempt++) {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 10000);
            try {
                const res = await fetch(url, { signal: controller.signal });
                clearTimeout(timeout);
                if (res.ok) return res;
                if (res.status >= 400 && res.status < 500) throw new Error(`HTTP ${res.status}`);
                if (attempt === retries) throw new Error(`HTTP ${res.status}`);
                // 5xx with retries left: backoff then retry
                await new Promise(r => setTimeout(r, delay * Math.pow(2, attempt)));
            } catch (err) {
                clearTimeout(timeout);
                if (attempt === retries) throw err;
                await new Promise(r => setTimeout(r, delay * Math.pow(2, attempt)));
            }
        }
        throw new Error('resilientFetch: exhausted retries');
    }
    let direitosData = null;
    let fontesData = null;
    let docsMestreData = null;
    let instituicoesData = null;
    let orgaosEstaduaisData = null;
    let municipiosData = null;        // IBGE snapshot: [{id,n,u,k}, ...] — populated by loadData
    let municipiosByKey = null;       // Map<k, {id,n,u,k}> for O(1) exact lookup
    let classificacaoData = null;
    let jsonMeta = null;
    let UPPERCASE_ONLY_TERMS = new Set();
    let CID_RANGE_MAP = {};
    let KEYWORD_MAP = {};
    let dicionarioData = null;  // dicionario_pcd.json deficiencies for search enrichment
    let legalReviewMeta = null;
    let legalReviewByCategory = {};
    const STORAGE_PREFIX = 'nossodireito_';
    const DB_NAME = 'NossoDireitoDB';
    const DB_VERSION = 2;
    const STORE_NAME = 'documentos';
    const CRYPTO_STORE = 'crypto_keys';
    const CRYPTO_KEY_ID = 'master_aes_key';
    const MAX_FILES = 5;
    const MAX_FILE_SIZE = 5 * 1024 * 1024;
    const FILE_TTL_MINUTES = 15;
    const ALLOWED_TYPES = [
        'application/pdf',
        'image/jpeg',
        'image/png',
    ];
    const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
    const CRYPTO_AVAILABLE = typeof crypto !== 'undefined' && typeof crypto.subtle !== 'undefined';
    const A11Y_FONT_KEY = STORAGE_PREFIX + 'font_size';
    const A11Y_CONTRAST_KEY = STORAGE_PREFIX + 'high_contrast';
    const FONT_STEPS = [14, 15, 16, 18, 20, 22];
    const FONT_DEFAULT = 16;

    function setupAccessibilityPanel() {
        // Drawer controls
        const trigger = document.getElementById('a11yPanelTrigger');
        const overlay = document.getElementById('a11yOverlay');
        const drawer = document.getElementById('a11yDrawer');
        const closeBtn = document.getElementById('a11yDrawerClose');

        // Accessibility buttons inside drawer
        const btnDecrease = document.getElementById('a11yFontDecrease');
        const btnReset = document.getElementById('a11yFontReset');
        const btnIncrease = document.getElementById('a11yFontIncrease');
        const btnContrast = document.getElementById('a11yContrast');
        const btnLibras = document.getElementById('a11yLibras');

        // Drawer state
        let isDrawerOpen = false;

        // Drawer open/close functions
        function openDrawer() {
            isDrawerOpen = true;
            drawer.setAttribute('aria-hidden', 'false');
            overlay.setAttribute('aria-hidden', 'false');
            trigger.setAttribute('aria-expanded', 'true');

            // Trap focus
            const focusables = drawer.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusables.length > 0) {
                focusables[0].focus();
            }

            // Prevent body scroll
            document.body.style.overflow = 'hidden';
        }

        function closeDrawer() {
            isDrawerOpen = false;
            drawer.setAttribute('aria-hidden', 'true');
            overlay.setAttribute('aria-hidden', 'true');
            trigger.setAttribute('aria-expanded', 'false');

            // Restore body scroll
            document.body.style.overflow = '';

            // Return focus to trigger
            trigger.focus();
        }

        function toggleDrawer() {
            if (isDrawerOpen) {
                closeDrawer();
            } else {
                openDrawer();
            }
        }

        // Drawer event listeners
        if (trigger) trigger.addEventListener('click', toggleDrawer);
        if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
        if (overlay) overlay.addEventListener('click', closeDrawer);

        // Esc key to close
        if (drawer) {
            drawer.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    closeDrawer();
                }
            });
        }

        // Tab trap inside drawer
        if (drawer) {
            drawer.addEventListener('keydown', (e) => {
                if (e.key !== 'Tab') return;

                const focusables = drawer.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                const first = focusables[0];
                const last = focusables[focusables.length - 1];

                if (e.shiftKey && document.activeElement === first) {
                    last.focus();
                    e.preventDefault();
                } else if (!e.shiftKey && document.activeElement === last) {
                    first.focus();
                    e.preventDefault();
                }
            });
        }
        let currentSize = FONT_DEFAULT;
        try {
            const saved = localStorage.getItem(A11Y_FONT_KEY);
            if (saved && FONT_STEPS.includes(Number(saved))) currentSize = Number(saved);
        } catch (_) { }
        applyFontSize(currentSize);
        if (btnDecrease) btnDecrease.addEventListener('click', () => {
            const idx = FONT_STEPS.indexOf(currentSize);
            if (idx > 0) { currentSize = FONT_STEPS[idx - 1]; applyFontSize(currentSize); }
        });
        if (btnReset) btnReset.addEventListener('click', () => {
            currentSize = FONT_DEFAULT; applyFontSize(currentSize);
        });
        if (btnIncrease) btnIncrease.addEventListener('click', () => {
            const idx = FONT_STEPS.indexOf(currentSize);
            if (idx < FONT_STEPS.length - 1) { currentSize = FONT_STEPS[idx + 1]; applyFontSize(currentSize); }
        });
        function applyFontSize(size) {
            document.documentElement.style.fontSize = size + 'px';
            try { localStorage.setItem(A11Y_FONT_KEY, String(size)); } catch (_) { }
        }
        let contrastOn = false;
        try {
            contrastOn = localStorage.getItem(A11Y_CONTRAST_KEY) === 'true';
        } catch (_) { }
        if (contrastOn) toggleContrast(true);
        if (btnContrast) btnContrast.addEventListener('click', () => {
            contrastOn = !contrastOn;
            toggleContrast(contrastOn);
        });
        function toggleContrast(on) {
            document.documentElement.classList.toggle('high-contrast', on);
            if (btnContrast) {
                btnContrast.setAttribute('aria-pressed', String(on));
                // Update state text
                const stateEl = btnContrast.querySelector('.a11y-toggle-state');
                if (stateEl) {
                    stateEl.textContent = on ? 'Ativado' : 'Desativado';
                }
            }
            try { localStorage.setItem(A11Y_CONTRAST_KEY, String(on)); } catch (_) { }
        }
        let vlOK = false, vlP = null;
        function initVL() {
            try {
                new window.VLibras.Widget('https://vlibras.gov.br/app');
                /* VLibras sets window.onload to inject its DOM (imgs, plugin HTML).
                   When lazy-loaded after page load, onload never fires — trigger it. */
                if (typeof window.onload === 'function') { try { window.onload(); } catch (_) { } }
                vlOK = true;
            } catch (_) { }
        }
        function ldVL(u) { return new Promise((y, n) => { const s = document.createElement('script'); s.src = u; s.onload = () => window.VLibras ? (initVL(), y()) : n(); s.onerror = n; document.head.appendChild(s); }); }
        const VLC = 'https://cdn.jsdelivr.net/gh/spbgovbr-vlibras/vlibras-portal@dev/app/vlibras-plugin.js';
        function ensureVL() { if (vlOK) return Promise.resolve(!0); if (window.VLibras) { initVL(); return Promise.resolve(!0); } if (!vlP) vlP = ldVL('https://vlibras.gov.br/app/vlibras-plugin.js').catch(() => ldVL(VLC)).then(() => !0, () => { vlP = null; return !1; }); return vlP; }
        if (window.VLibras) initVL();
        if (btnLibras) btnLibras.addEventListener('click', async () => {
            btnLibras.disabled = true; btnLibras.textContent = '⏳ Carregando...';
            try {
                if (!await ensureVL()) { showToast('VLibras indisponível. Tente novamente mais tarde.', 'error'); return; }
                /* Poll for VLibras DOM: look for img[src] (preferred) or any img child
                   inside [vw-access-button], then programmatically click to open panel. */
                await new Promise(r => {
                    let c = 0; const iv = setInterval(() => {
                        const ab = document.querySelector('[vw-access-button]');
                        const img = ab && (ab.querySelector('img[src]') || ab.querySelector('img'));
                        if (img) { clearInterval(iv); ab.click(); r(); }
                        else if (++c > 40) { clearInterval(iv); showToast('VLibras carregou mas o painel não apareceu. Recarregue a página.', 'warning'); r(); }
                    }, 200);
                });
            } finally { btnLibras.disabled = false; btnLibras.textContent = '🤟 Libras'; }
        });
        const btnReadAloud = document.getElementById('a11yReadAloud');
        const TTS_AVAILABLE = typeof speechSynthesis !== 'undefined';
        let ttsActive = false;
        let currentUtterance = null;
        let keepAliveInterval = null;
        let currentChunks = [];
        let currentChunkIndex = 0;
        function preprocessTextForTTS(text) {
            return text
                .replace(/\s+/g, ' ')
                .replace(/\n{3,}/g, '\n\n')
                .replace(/\bArt\.?\s*(\d+)/gi, 'Artigo $1')
                .replace(/§\s*(\d+)/g, 'parágrafo $1')
                .replace(/Inc\.?\s*/gi, 'inciso ')
                .replace(/cf\.?\s+/gi, 'conforme ')
                .replace(/\bvs\.?\s+/gi, 'versus ')
                .replace(/\bDr\.\s+/g, 'Doutor ')
                .replace(/\bDra\.\s+/g, 'Doutora ')
                .replace(/\bProf\.\s+/g, 'Professor ')
                .replace(/\bSr\.\s+/g, 'Senhor ')
                .replace(/\bSra\.\s+/g, 'Senhora ')
                .replace(/\bINSS\b/g, 'I-N-S-S')
                .replace(/\bBPC\b/g, 'B-P-C')
                .replace(/\bCID\b/g, 'C-I-D')
                .replace(/\bCPF\b/g, 'C-P-F')
                .replace(/\bRG\b/g, 'R-G')
                .trim();
        }
        function splitIntoChunks(text) {
            const MIN_CHUNK = 1200;
            const MAX_CHUNK = 1600;
            const paragraphs = text.split(/\n\n+/);
            const hasManyParagraphs = paragraphs.length > 3;
            if (text.length <= 1800 && !hasManyParagraphs) {
                return [text];
            }

            const sentences = text.match(/[^.!?\n]+(?:[.!?\n]+|$)/g) || [text];
            const chunks = [];
            let currentChunk = '';
            for (const sentence of sentences) {
                const potentialLength = currentChunk.length + sentence.length;
                if (potentialLength > MAX_CHUNK && currentChunk.length >= MIN_CHUNK) {
                    chunks.push(currentChunk.trim());
                    currentChunk = sentence;
                } else {
                    currentChunk += sentence;
                }
            }
            if (currentChunk.trim().length > 0) {
                chunks.push(currentChunk.trim());
            }
            return chunks.length > 0 ? chunks : [text];
        }
        let _voicePromise = null;
        function waitForVoices() {
            if (_voicePromise) return _voicePromise;
            _voicePromise = new Promise((resolve) => {
                const voices = speechSynthesis.getVoices();
                if (voices.length) return resolve(voices);
                const timeout = setTimeout(() => {
                    speechSynthesis.onvoiceschanged = null;
                    resolve(speechSynthesis.getVoices());
                }, 6000); // 6s: iOS Safari can take 5s+ to enumerate voices
                speechSynthesis.onvoiceschanged = () => {
                    clearTimeout(timeout);
                    const loadedVoices = speechSynthesis.getVoices();
                    speechSynthesis.onvoiceschanged = null;
                    resolve(loadedVoices);
                };
            });
            return _voicePromise;
        }
        function getTextToRead() {
            const selection = window.getSelection();
            if (selection && selection.toString().trim().length > 0) {
                const selectedText = selection.toString().trim();
                const wordCount = selectedText.split(/\s+/).length;
                if (wordCount >= 3) {
                    return selectedText;
                }
            }
            // Use runtime visibility check instead of CSS attribute selector
            // (covers display:none, hidden, programmatic visibility changes)
            const allSections = document.querySelectorAll('main section');
            let bestSection = null;
            let bestDistance = Infinity;
            for (const section of allSections) {
                if (section.hidden) continue;
                const rect = section.getBoundingClientRect();
                if (rect.height === 0) continue; // skip display:none / collapsed
                const distance = Math.abs(rect.top - 80);
                if (distance < bestDistance) {
                    bestDistance = distance;
                    bestSection = section;
                }
            }
            if (!bestSection) return '';
            const clone = bestSection.cloneNode(true);
            clone.querySelectorAll('script, style, input, button, [aria-hidden="true"]').forEach(el => el.remove());
            const text = clone.textContent
                .replace(/\s+/g, ' ')
                // Remove qualquer pictograma estendido (emoji) — usa Unicode property escape
                // para evitar duplicatas no character class (CodeQL js/regex/duplicate-in-character-class).
                .replace(/\p{Extended_Pictographic}\uFE0F?/gu, '')
                .trim();
            return text;
        }
        function getBestPtBrVoice(voices) {
            let savedVoiceName = null;
            try { savedVoiceName = localStorage.getItem(STORAGE_PREFIX + 'tts_voice'); } catch { /* private browsing */ }
            if (savedVoiceName) {
                const savedVoice = voices.find(v => v.name === savedVoiceName);
                if (savedVoice) {
                    return savedVoice;
                }
            }
            let voice = voices.find(v => v.lang === 'pt-BR');
            if (voice) return voice;
            voice = voices.find(v => v.lang === 'pt-PT');
            if (voice) return voice;
            voice = voices.find(v => v.lang.startsWith('pt'));
            if (voice) return voice;
            if (voices.length === 0) {
                console.warn('[TTS] Nenhuma voz disponível no sistema.');
                return null;
            }
            console.warn('[TTS] Nenhuma voz pt encontrada. Usando:', voices[0].name, voices[0].lang);
            showToast('\u26a0\ufe0f Seu navegador pode n\u00e3o suportar portugu\u00eas. A leitura pode estar em outro idioma. Instale vozes pt-BR nas configura\u00e7\u00f5es do sistema.', 'warning');
            return voices[0];
        }
        async function startReading() {
            if (!('speechSynthesis' in window)) {
                showToast('Seu navegador não suporta leitura em voz.', 'warning');
                return;
            }
            const text = getTextToRead();
            if (!text || text.trim().length < 5) {
                showToast('Não há conteúdo para ler. Selecione um texto ou navegue até uma seção.', 'info');
                return;
            }
            stopReading();
            const voices = await waitForVoices();
            if (!voices.length) {
                showToast('Nenhuma voz disponível no sistema.', 'warning');
                return;
            }
            const voice = getBestPtBrVoice(voices);
            if (voice) {

                try {
                    localStorage.setItem(STORAGE_PREFIX + 'tts_voice', voice.name);
                } catch (_) { }
            } else {
                console.warn('[TTS] Nenhuma voz disponível! Tentando voz padrão do sistema.');
            }
            const processedText = preprocessTextForTTS(text);
            currentChunks = splitIntoChunks(processedText);
            currentChunkIndex = 0;
            console.info('[TTS] Iniciando leitura | voz:', voice ? voice.name : 'padrão', '| chars:', text.length, '| processado:', processedText.length, '| chunks:', currentChunks.length);
            ttsActive = true;
            speakChunk(voice, processedText.length);
        }
        function speakChunk(voice, originalTextLength) {
            if (!ttsActive || currentChunkIndex >= currentChunks.length) {
                stopReading();
                return;
            }
            const chunk = currentChunks[currentChunkIndex];
            const utterance = new SpeechSynthesisUtterance(chunk);
            utterance.voice = voice;
            utterance.lang = voice ? voice.lang : 'pt-BR';
            if (originalTextLength < 300) {
                utterance.rate = 1.05;
            } else if (originalTextLength > 1500 || chunk.includes('Artigo') || chunk.includes('parágrafo')) {
                utterance.rate = 0.9;
            } else {
                utterance.rate = 1.0;
            }
            utterance.pitch = 1.0;
            currentUtterance = utterance;
            if (chunk.length > 200 && currentChunks.length === 1) {
                // Chrome TTS keepalive (pause/resume workaround) - skip on Safari/iOS where it breaks TTS
                // Use vendor check instead of fragile UA regex (catches iPadOS desktop mode + Samsung Internet)
                const isSafari = typeof navigator !== 'undefined' && navigator.vendor === 'Apple Computer, Inc.';
                if (!isSafari) {
                    keepAliveInterval = setInterval(() => {
                        if (!ttsActive) return;
                        if (speechSynthesis.speaking && !speechSynthesis.paused) {
                            speechSynthesis.pause();
                            setTimeout(() => speechSynthesis.resume(), 50);
                        }
                    }, 12000);
                }
            }
            const handleEnd = () => {
                if (keepAliveInterval) {
                    clearInterval(keepAliveInterval);
                    keepAliveInterval = null;
                }
                currentChunkIndex++;
                if (currentChunkIndex < currentChunks.length && ttsActive) {
                    speakChunk(voice, originalTextLength);
                } else {
                    stopReading();
                }
            };
            const handleError = (e) => {
                if (keepAliveInterval) {
                    clearInterval(keepAliveInterval);
                    keepAliveInterval = null;
                }
                stopReading();
                if (e.error === 'canceled' || e.error === 'interrupted') {

                    return;
                }
                if (e.error === 'not-allowed') {
                    showToast('O navegador bloqueou o áudio. Clique novamente para ouvir.', 'warning');
                    return;
                }
                if (e.error === 'audio-busy') {
                    showToast('Outro áudio está em uso no dispositivo.', 'warning');
                    return;
                }
                console.error('[TTS] Erro na síntese de voz:', e.error, e);
                const errorMsg = voice
                    ? `Erro ao reproduzir voz "${voice.name}": ${e.error}. Tente novamente ou use outro navegador.`
                    : 'Nenhuma voz instalada no sistema. Instale vozes pt-BR nas configurações do navegador.';
                showToast(errorMsg, 'warning');
            };
            utterance.onend = handleEnd;
            utterance.onerror = handleError;
            if (speechSynthesis.speaking || (typeof speechSynthesis.pending !== 'undefined' && speechSynthesis.pending)) {
                speechSynthesis.cancel();
            }
            speechSynthesis.speak(utterance);
            if (btnReadAloud && currentChunkIndex === 0) {
                const iconEl = btnReadAloud.querySelector('.a11y-toggle-icon');
                const labelEl = btnReadAloud.querySelector('.a11y-toggle-label');
                const stateEl = btnReadAloud.querySelector('.a11y-toggle-state');
                if (iconEl) iconEl.textContent = '⏹️';
                if (labelEl) labelEl.textContent = 'Parar';
                if (stateEl) stateEl.textContent = 'Ativo';
                btnReadAloud.setAttribute('aria-pressed', 'true');
            }
        }
        function stopReading() {
            ttsActive = false;
            if (keepAliveInterval) {
                clearInterval(keepAliveInterval);
                keepAliveInterval = null;
            }
            if (speechSynthesis.speaking || (typeof speechSynthesis.pending !== 'undefined' && speechSynthesis.pending)) {
                speechSynthesis.cancel();
            }
            currentUtterance = null;
            if (btnReadAloud) {
                const iconEl = btnReadAloud.querySelector('.a11y-toggle-icon');
                const labelEl = btnReadAloud.querySelector('.a11y-toggle-label');
                const stateEl = btnReadAloud.querySelector('.a11y-toggle-state');
                if (iconEl) iconEl.textContent = '🔊';
                if (labelEl) labelEl.textContent = 'Ouvir Página';
                if (stateEl) stateEl.textContent = 'Desativado';
                btnReadAloud.setAttribute('aria-pressed', 'false');
            }
        }
        async function toggleReadAloud() {
            if (ttsActive) {
                stopReading();
                await new Promise(r => setTimeout(r, 150));
            } else {
                await startReading();
            }
        }
        if (btnReadAloud && TTS_AVAILABLE) {
            btnReadAloud.addEventListener('click', toggleReadAloud);
        } else if (btnReadAloud && !TTS_AVAILABLE) {
            btnReadAloud.style.display = 'none';
        }
        waitForVoices().catch(() => { /* pre-warm voices; errors handled in startReading */ });
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && ttsActive) {

                stopReading();
            }
        });
        window.addEventListener('hashchange', () => {
            if (ttsActive) stopReading();
            /* SPA routing: navigate to detail view when hash changes to #direito/{id} */
            const hash = location.hash;
            if (hash.startsWith('#direito/')) {
                try {
                    const id = decodeURIComponent(hash.replace('#direito/', ''));
                    if (id && direitosData) showDetalhe(id, true);
                } catch (e) {
                    console.warn('Hash inválido:', hash, e);
                }
            } else if (hash && !hash.startsWith('#direito/')) {
                /* Navigating back to a section anchor — hide detail if visible */
                if (dom.detalheSection && dom.detalheSection.style.display !== 'none') {
                    dom.detalheSection.style.display = 'none';
                    if (dom.categoriasSection) dom.categoriasSection.style.display = '';
                    updateSectionAlternation();
                    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                    window.scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });
                }
            }
        });
    }

    let _pdfJsReady = typeof pdfjsLib !== 'undefined';
    function ensurePdfJs() {
        if (_pdfJsReady) return Promise.resolve();
        return new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            s.integrity = 'sha384-/1qUCSGwTur9vjf/z9lmu/eCUYbpOTgSjmpbMQZ1/CtX2v/WcAIKqRv+U1DUCG6e';
            s.crossOrigin = 'anonymous';
            s.onload = () => {
                pdfjsLib.GlobalWorkerOptions.workerSrc =
                    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                _pdfJsReady = true;
                resolve();
            };
            s.onerror = () => reject(new Error('Não foi possível carregar o leitor de PDF.'));
            document.head.appendChild(s);
        });
    }
    if (_pdfJsReady) {
        pdfjsLib.GlobalWorkerOptions.workerSrc =
            'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.setAttribute('role', type === 'error' || type === 'warning' ? 'alert' : 'status');
        toast.setAttribute('aria-live', type === 'error' || type === 'warning' ? 'assertive' : 'polite');
        document.body.appendChild(toast);
        setTimeout(() => { if (toast.parentNode) toast.remove(); }, 5000);
    }
    function confirmAction(msg, cb) {
        const d = document.createElement('dialog');
        if (typeof d.showModal !== 'function') {
            if (window.confirm(msg)) cb();
            return;
        }
        d.className = 'confirm-dialog';
        d.setAttribute('role', 'alertdialog');
        d.setAttribute('aria-label', msg);
        d.innerHTML = '<p>' + escapeHtml(msg) + '</p><div class="confirm-actions"><button>Cancelar</button><button class="btn-confirm">Confirmar</button></div>';
        document.body.appendChild(d);
        d.showModal();
        d.addEventListener('close', () => { if (d.parentNode) d.remove(); });
        d.onclick = e => { const btn = e.target.closest('button'); if (btn) { const ok = btn.classList.contains('btn-confirm'); d.close(); d.remove(); if (ok) cb(); } };
    }
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);
    let dom;
    function updateSectionAlternation() {
        const main = document.querySelector('main');
        if (!main) return;
        const visibleSections = Array.from(main.querySelectorAll(':scope > .section'))
            .filter(s => s.style.display !== 'none' && !s.hidden);
        visibleSections.forEach((section, i) => {
            if (i % 2 === 1) {
                section.classList.add('section-alt');
            } else {
                section.classList.remove('section-alt');
            }
        });
    }

    /**
     * Yield control to the main thread so the browser can paint and handle
     * input between initialization phases.  Keeps each task under ~50 ms
     * (Long Task threshold), improving TBT and INP.
     */
    function yieldToMain() {
        return new Promise(resolve => setTimeout(resolve, 0));
    }

    async function init() {
        // Initialize DOM references after DOM is loaded
        dom = {
            menuToggle: $('#menuToggle'),
            navLinks: $('#navLinks'),
            searchInput: $('#searchInput'),
            searchBtn: $('#searchBtn'),
            searchResults: $('#searchResults'),
            categoryGrid: $('#categoryGrid'),
            trilhaTabs: $('#trilhaTabs'),
            detalheSection: $('#detalhe'),
            detalheContent: $('#detalheContent'),
            voltarBtn: $('#voltarBtn'),
            categoriasSection: $('#categorias'),
            lastUpdate: $('#lastUpdate'),
            uploadZone: $('#uploadZone'),
            fileInput: $('#fileInput'),
            fileList: $('#fileList'),
            deleteAllFiles: $('#deleteAllFiles'),
            docsChecklist: $('#docsChecklist'),
            analysisResults: $('#analysisResults'),
            analysisLoading: $('#analysisLoading'),
            analysisContent: $('#analysisContent'),
            closeAnalysis: $('#closeAnalysis'),
            exportPdf: $('#exportPdf'),
            instituicoesGrid: $('#instituicoesGrid'),
            orgaosEstaduaisGrid: $('#orgaosEstaduaisGrid'),
            classificacaoGrid: $('#classificacaoGrid'),
            transLastUpdate: $('#transLastUpdate'),
            transVersion: $('#transVersion'),
            footerVersion: $('#footerVersion'),
            dataAviso: $('#dataAviso'),
            linksGrid: $('#linksGrid'),
            stalenessBanner: $('#stalenessBanner'),
            staleDays: $('#staleDays'),
            heroCatCount: $('#heroCatCount'),
            heroFontesCount: $('#heroFontesCount'),
        };
        // Security: passamos 'name' como argumento separado em vez de
        // interpolar no template literal — evita CodeQL js/tainted-format-string
        // (mesmo sendo strings literais nos call sites, o analisador trata como
        // tainted; argumentos extras não são interpretados como format spec).
        const safeRun = (name, fn) => {
            try { fn(); } catch (e) { console.error('[init]', name, 'falhou:', e); }
        };
        const safeRunAsync = async (name, fn) => {
            try { await fn(); } catch (e) { console.error('[init]', name, 'falhou:', e); }
        };
        // ── Phase 1: Critical above-fold (nav, search, a11y, data) ──
        // setupAccessibilityPanel PRECEDE loadData/renderCategories porque
        // não depende de dados e é prioridade WCAG (usuário com baixa visão
        // pode precisar aumentar a fonte ANTES do site terminar de carregar).
        // Antes ficava em Phase 2 e em conexões lentas (iPhone Safari 3G/4G)
        // o usuário tocava no botão flutuante antes do handler ser anexado
        // — tap se perdia silenciosamente.
        safeRun('setupAccessibilityPanel', setupAccessibilityPanel);
        safeRun('setupNavigation', setupNavigation);
        safeRun('setupSearch', setupSearch);
        await safeRunAsync('loadData', loadData);
        safeRun('renderCategories', renderCategories);
        safeRun('renderHeroStats', renderHeroStats);

        // Yield to main thread so browser can paint above-fold content
        await yieldToMain();

        // ── Phase 2: Interactive features ──
        safeRun('setupSkipLinks', setupSkipLinks);
        safeRun('setupFooter', setupFooter);
        safeRun('setupBackToTop', setupBackToTop);
        safeRunAsync('enrichGovBr', enrichGovBr);
        safeRun('setupFooterVersion', setupFooterVersion);

        // Yield again before heavy DOM rendering
        await yieldToMain();

        // ── Phase 3: Below-fold rendering ──
        safeRun('renderTransparency', renderTransparency);
        safeRun('renderDocsChecklist', renderDocsChecklist);
        /* Defer below-fold sections to reduce initial DOM size (~500 fewer elements).
           They render when scrolled into the viewport (or immediately on hash nav). */
        const deferredSections = [
            { id: 'links', fn: renderLinksUteis },
            { id: 'classificacao', fn: renderClassificacao },
            { id: 'orgaos-estaduais', fn: renderOrgaosEstaduais },
            { id: 'instituicoes', fn: renderInstituicoes },
        ];
        const deferredRendered = new Set();
        function renderDeferred(sectionId) {
            const entry = deferredSections.find(s => s.id === sectionId);
            if (entry && !deferredRendered.has(sectionId)) {
                deferredRendered.add(sectionId);
                safeRun('deferred:' + sectionId, entry.fn);
            }
        }
        if ('IntersectionObserver' in window) {
            const io = new IntersectionObserver((entries) => {
                entries.forEach(e => {
                    if (e.isIntersecting) {
                        renderDeferred(e.target.id);
                        io.unobserve(e.target);
                    }
                });
            }, { rootMargin: '200px' });
            deferredSections.forEach(s => {
                const el = document.getElementById(s.id);
                if (el) io.observe(el);
            });
        } else {
            deferredSections.forEach(s => safeRun(s.id, s.fn));
        }
        /* If page loaded with a hash pointing to a deferred section, render it now */
        const hashTarget = location.hash.replace('#', '');
        if (hashTarget) renderDeferred(hashTarget);
        safeRun('checkStaleness', checkStaleness);

        // Yield before upload/file operations (IndexedDB access)
        await yieldToMain();

        // ── Phase 4: Upload, analysis, file management ──
        safeRun('setupUpload', setupUpload);
        safeRun('setupAnalysis', setupAnalysis);
        await safeRunAsync('cleanupExpiredFiles', cleanupExpiredFiles);
        await safeRunAsync('renderFileList', renderFileList);
        safeRun('updateSectionAlternation', updateSectionAlternation);
        /* Deep-link: handle #direito/{id} on cold page load */
        const initialHash = location.hash;
        if (initialHash.startsWith('#direito/')) {
            try {
                const deepId = decodeURIComponent(initialHash.replace('#direito/', ''));
                if (deepId && direitosData) {
                    showDetalhe(deepId, true);
                }
            } catch (e) {
                console.warn('Hash inicial inválido:', initialHash, e);
            }
        }
        // Remove SEO-only content from DOM to reduce DOM size (crawlers already parsed it)
        const seoContent = document.getElementById('seo-content');
        if (seoContent) seoContent.remove();
        // Handle ?q= URL parameter (SearchAction schema support)
        try {
            const urlQ = new URLSearchParams(window.location.search).get('q');
            if (urlQ && dom.searchInput) {
                dom.searchInput.value = urlQ;
                dom.searchInput.dispatchEvent(new Event('input'));
                const consultar = document.getElementById('consultar');
                if (consultar) consultar.scrollIntoView({ behavior: 'smooth' });
            }
        } catch (_qErr) { /* ignore invalid URL params */ }
        setInterval(async () => {
            const removed = await cleanupExpiredFiles();
            if (removed > 0) await renderFileList();
        }, 60000);
    }

    /**
     * setupSkipLinks — eMAG 4.1 accesskey focus fix.
     * HTML accesskey on <a href="#target"> just follows the link (scroll).
     * On macOS (Ctrl+Opt+key) and some browsers the target element never
     * receives keyboard focus. This handler intercepts skip-link clicks
     * (which the browser fires after the accesskey combo) and explicitly
     * calls .focus() on the destination element.
     */
    function setupSkipLinks() {
        document.querySelectorAll('a.skip-link[accesskey]').forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                if (!href || !href.startsWith('#')) return;
                const targetId = href.slice(1);
                const target = document.getElementById(targetId);
                if (!target) return;
                e.preventDefault();
                // Make non-focusable elements focusable temporarily
                if (!target.hasAttribute('tabindex') &&
                    !['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON', 'A'].includes(target.tagName)) {
                    target.setAttribute('tabindex', '-1');
                }
                target.focus({ preventScroll: false });
                // v1.43.22 — block:'start' (não 'center') para alinhar com o restante
                // da nav. 'center' levava o destino para o meio da tela, contradizendo
                // o scroll-padding-top: 80px do html.
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });
    }

    function setupNavigation() {
        if (!dom.menuToggle || !dom.navLinks) return;
        dom.menuToggle.addEventListener('click', () => {
            const open = dom.navLinks.classList.toggle('open');
            dom.menuToggle.classList.toggle('open', open);
            dom.menuToggle.setAttribute('aria-expanded', String(open));
            dom.menuToggle.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && dom.navLinks.classList.contains('open')) {
                dom.navLinks.classList.remove('open');
                dom.menuToggle.classList.remove('open');
                dom.menuToggle.setAttribute('aria-expanded', 'false');
                dom.menuToggle.setAttribute('aria-label', 'Abrir menu');
                dom.menuToggle.focus();
            }
        });
        dom.navLinks.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', (e) => {
                dom.navLinks.classList.remove('open');
                dom.menuToggle.classList.remove('open');
                dom.menuToggle.setAttribute('aria-expanded', 'false');
                dom.menuToggle.setAttribute('aria-label', 'Abrir menu');

                /* v1.43.18 — Anchor scroll natural (sem hacks).
                 * scroll-padding-top: 80px (CSS html) + .section padding 40px 0
                 * fazem o h2 da seção alvo aterrissar em y=120 (40px de respiro
                 * acima dele, 56px abaixo da navbar). Tabpanels de Referências
                 * e #disclaimerInline herdam o mesmo offset de 80px naturalmente.
                 *
                 * Para alvos dentro de tabpanels ocultos (Apoio→#instituicoes,
                 * Aviso→#disclaimerInline, e os subitens de Referências), a
                 * ativação da tab + scroll é feita em setupReferenciasTabs via rAF
                 * para esperar o layout do painel recém-revelado. Aqui apenas
                 * abrimos passagem (return) para o handler global tratar. */
                const href = link.getAttribute('href');
                if (!href || !href.startsWith('#') || href.length < 2) return;
                const REF_HASHES = new Set(['#links', '#classificacao', '#orgaos-estaduais', '#instituicoes', '#transparencia', '#compromissoAtualizacao', '#disclaimerInline']);
                if (REF_HASHES.has(href)) return;
                const target = document.querySelector(href);
                if (!target) return;
                e.preventDefault();
                const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                if (history.replaceState) history.replaceState(null, '', href);
                // Garante layout estável após fechar drawer mobile antes do scroll.
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        if (href === '#inicio') {
                            window.scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });
                        } else {
                            target.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
                        }
                    });
                });
            });
        });
        const sections = $$('section[id]');
        const navAnchors = dom.navLinks.querySelectorAll('a');
        if (!('IntersectionObserver' in window)) return;
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const id = entry.target.id;
                        navAnchors.forEach((a) => {
                            const isActive = a.getAttribute('href') === `#${id}`;
                            a.classList.toggle('active', isActive);
                            if (isActive) {
                                a.setAttribute('aria-current', 'true');
                            } else {
                                a.removeAttribute('aria-current');
                            }
                        });
                    }
                });
            },
            { rootMargin: '-100px 0px -60% 0px' }
        );
        sections.forEach((s) => observer.observe(s));
        if (dom.voltarBtn) dom.voltarBtn.addEventListener('click', () => {
            dom.detalheSection.style.display = 'none';
            dom.categoriasSection.style.display = '';
            dom.analysisResults.style.display = 'none';
            updateSectionAlternation();
            history.pushState({ view: 'categorias' }, '', '#categorias');
            const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            dom.categoriasSection.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
            const h2 = dom.categoriasSection.querySelector('h2');
            if (h2) { h2.setAttribute('tabindex', '-1'); h2.focus({ preventScroll: true }); }
        });
        window.addEventListener('popstate', async (e) => {
            if (e.state && e.state.view === 'detalhe' && e.state.id) {
                showDetalhe(e.state.id, true);
            } else if (e.state && e.state.view === 'analysis') {
                // Recuperar análise do cache ao voltar
                if (typeof window.ANALYSIS_CACHE !== 'undefined') {
                    const cached = await window.ANALYSIS_CACHE.retrieve();
                    if (cached && dom.analysisResults) {
                        dom.analysisResults.style.display = '';
                        if (dom.categoriasSection) dom.categoriasSection.style.display = 'none';
                        renderAnalysisResults(cached.results, cached.fileNames, cached.hasPdf, cached.errors, cached.aiResult, cached.aiAttempted);
                        const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                        dom.analysisResults.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
                        return;
                    }
                }
                // Fallback: ir para categorias se não houver cache
                if (dom.detalheSection && dom.categoriasSection) {
                    dom.detalheSection.style.display = 'none';
                    dom.categoriasSection.style.display = '';
                    dom.analysisResults.style.display = 'none';
                    updateSectionAlternation();
                }
            } else if (dom.detalheSection && dom.categoriasSection) {
                dom.detalheSection.style.display = 'none';
                dom.categoriasSection.style.display = '';
                if (dom.analysisResults) dom.analysisResults.style.display = 'none';
                updateSectionAlternation();
            }
        });
    }
    async function loadData() {
        try {
            const res = (await _earlyDireitos) || await resilientFetch('data/direitos.json');
            const json = await res.json();
            direitosData = deepFreeze(json.categorias);
            fontesData = deepFreeze(json.fontes || []);
            docsMestreData = deepFreeze(json.documentos_mestre || []);
            instituicoesData = deepFreeze(json.instituicoes_apoio || []);
            orgaosEstaduaisData = deepFreeze(json.orgaos_estaduais || []);
            classificacaoData = deepFreeze(json.classificacao_deficiencia || []);
            jsonMeta = Object.freeze({
                versao: json.versao,
                ultima_atualizacao: json.ultima_atualizacao,
                proxima_revisao: json.proxima_revisao,
            });
            if (json.ultima_atualizacao && dom.lastUpdate) {
                dom.lastUpdate.textContent = formatDate(json.ultima_atualizacao);
            }
        } catch (err) {
            console.error('Erro ao carregar dados:', err);
            if (dom.categoryGrid) {
                dom.categoryGrid.innerHTML = `
<div style="grid-column: 1/-1; text-align:center; padding:32px; color:var(--text-muted);">
<p>⚠️ Não foi possível carregar os dados.</p>
<p style="font-size:0.9rem;">Verifique se o arquivo <code>data/direitos.json</code> está acessível.</p>
</div>`;
            }
        }
        try {
            const meRes = (await _earlyMatching) || await resilientFetch('data/matching_engine.json');
            const me = await meRes.json();
            UPPERCASE_ONLY_TERMS = Object.freeze(new Set(me.uppercase_only_terms));
            CID_RANGE_MAP = deepFreeze(me.cid_range_map);
            KEYWORD_MAP = deepFreeze(me.keyword_map);
        } catch (err) {
            console.warn('Motor de correspondência não carregou — análise de documentos pode ser limitada:', err.message);
        }
        // Load dicionario_pcd.json and merge synonyms/keywords into KEYWORD_MAP
        try {
            const dicRes = (await _earlyDicionario) || await resilientFetch('data/dicionario_pcd.json');
            const dic = await dicRes.json();
            dicionarioData = dic.deficiencias || [];
            // Enrich KEYWORD_MAP with dicionario synonyms and keywords
            // KEYWORD_MAP is frozen, so build a mutable copy
            const enriched = Object.assign({}, KEYWORD_MAP);
            dicionarioData.forEach((def) => {
                const allTerms = [
                    ...(def.keywords_busca || []),
                    ...(def.sinonimos || []),
                    ...(def.cid10 || []),
                    ...(Array.isArray(def.cid11) ? def.cid11 : (def.cid11 ? [def.cid11] : [])),
                    def.nome,
                ];
                const cats = def.beneficios_elegiveis || [];
                allTerms.forEach((term) => {
                    const normTerm = normalizeText(term);
                    if (!normTerm || normTerm.length < 2) return;
                    if (enriched[normTerm]) {
                        // Merge categories without duplicates, keep higher weight
                        const existing = enriched[normTerm];
                        const merged = new Set([...existing.cats, ...cats]);
                        enriched[normTerm] = { cats: Array.from(merged), weight: Math.max(existing.weight, 5) };
                    } else {
                        enriched[normTerm] = { cats: [...cats], weight: 5 };
                    }
                });
            });
            KEYWORD_MAP = deepFreeze(enriched);
        } catch (err) {
            console.warn('Dicionário PcD não carregou — busca por sinônimos limitada:', err.message);
        }
        // Load optional legal-review sidecar file for human-validation warnings.
        // Non-fatal by design: app must keep working even without this file.
        try {
            const reviewRes = (await _earlyLegalReview) || await resilientFetch('data/revisao_juridica.json');
            const review = await reviewRes.json();
            legalReviewMeta = Object.freeze({
                versao: review.versao || null,
                ultima_atualizacao: review.ultima_atualizacao || null,
                issue: review.issue || null,
            });
            const byCategory = {};
            (review.itens || []).forEach((item) => {
                if (!item || item.status !== 'PENDING_HUMAN_REVIEW') return;
                const categories = Array.isArray(item.categoria_ids) ? item.categoria_ids : [];
                const normalized = deepFreeze({
                    id: item.id || '',
                    issue: Number.isInteger(item.issue) ? item.issue : null,
                    issue_url: item.issue_url || '',
                    titulo: item.titulo || 'Item sob revisão jurídica',
                    aviso_curto: item.aviso_curto || 'Legislação em verificação jurídica humana.',
                    nota_sistema: item.nota_sistema || '',
                });
                categories.forEach((catId) => {
                    if (!byCategory[catId]) byCategory[catId] = [];
                    byCategory[catId].push(normalized);
                });
            });
            legalReviewByCategory = deepFreeze(byCategory);
        } catch (err) {
            console.warn('Arquivo de revisão jurídica não carregou — avisos de validação humana podem ficar indisponíveis:', err.message);
        }
        // Load IBGE municipios snapshot (5570 entries, ~80 KB gzipped).
        // Non-fatal: detectLocation falls back to UF-only detection if absent.
        try {
            const muniRes = (await _earlyMunicipios) || await resilientFetch('data/municipios_br.json');
            const muni = await muniRes.json();
            municipiosData = deepFreeze(muni.municipios || []);
            const byKey = new Map();
            municipiosData.forEach((m) => { byKey.set(m.k, m); });
            municipiosByKey = byKey;  // Map can't be frozen but contents are
        } catch (err) {
            console.warn('Snapshot de municípios não carregou — detecção limitada a UF/estado:', err.message);
        }
    }
    async function enrichGovBr() {
        if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') return;
        try {
            const _gc = new AbortController();
            const _gt = setTimeout(() => _gc.abort(), 4000);
            const r = await fetch('/api/govbr-servico/10783',
                { signal: _gc.signal });
            clearTimeout(_gt);
            if (r.ok) sessionStorage.setItem('govbr_10783', '1');
        } catch { }
    }
    function renderCategories() {
        if (!direitosData || !dom.categoryGrid) {
            console.warn('renderCategories: dados ou elemento faltando');
            return;
        }

        dom.categoryGrid.innerHTML = direitosData
            .map(
                (cat) => `
<div class="category-card" tabindex="0" role="button"
aria-label="Ver detalhes sobre ${escapeHtml(cat.titulo)}"
data-id="${cat.id}"
data-trilha="${escapeHtml(getTrilhaId(cat.id))}">
<h3>${escapeHtml(cat.titulo)}</h3>
</div>`
            )
            .join('');

        dom.categoryGrid.querySelectorAll('.category-card').forEach((card) => {
            card.addEventListener('click', () => showDetalhe(card.dataset.id));
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    showDetalhe(card.dataset.id);
                }
            });
        });

        renderTrilhaTabs();
    }

    // ---------- Trilhas (agrupamento de categorias) ----------
    // Ordem das trilhas: "Todas" vem primeiro (default) para que o usuário que
    // clica em "Categorias" no menu veja TODAS as 42 categorias e use os botões
    // por área para filtrar. Isto resolve a confusão de filtro silencioso
    // (issue UX: usuário não percebia que os botões eram filtros quando o
    // default mostrava apenas uma trilha).
    const TRILHAS = [
        { id: 'todas', label: 'Todas', icone: '📋', descricao: 'Lista completa dos 42 direitos', ids: null },
        {
            id: 'renda', label: 'Renda', icone: '💰',
            descricao: 'BPC, auxílios, isenções e saques especiais',
            ids: ['bpc', 'auxilio_inclusao', 'bolsa_familia', 'fgts', 'saque_fgts_doenca_grave', 'pensao_zika', 'tarifa_social_energia', 'isencao_ir'],
        },
        {
            id: 'saude', label: 'Saúde', icone: '🏥',
            descricao: 'SUS, plano de saúde, reabilitação e tecnologia assistiva',
            ids: ['sus_terapias', 'plano_saude', 'reabilitacao', 'caa_comunicacao_alternativa', 'tecnologia_assistiva'],
        },
        {
            id: 'educacao', label: 'Educação', icone: '🎓',
            descricao: 'Escola inclusiva, ProUni, FIES e SISU',
            ids: ['educacao', 'prouni_fies_sisu'],
        },
        {
            id: 'trabalho', label: 'Trabalho', icone: '💼',
            descricao: 'Cota PcD, horário especial e aposentadoria especial',
            ids: ['trabalho', 'cota_emprego_pcd_empresa', 'horario_especial_servidor_pcd', 'aposentadoria_especial_pcd'],
        },
        {
            id: 'mobilidade', label: 'Mobilidade', icone: '🚌',
            descricao: 'Transporte, estacionamento, IPVA e turismo acessível',
            ids: ['transporte', 'estacionamento_especial', 'isencoes_tributarias', 'turismo_acessivel', 'moradia'],
        },
        {
            id: 'cidadania', label: 'Cidadania', icone: '⚖️',
            descricao: 'CIPTEA, atendimento prioritário, capacidade legal e acessibilidade',
            ids: ['ciptea', 'atendimento_prioritario', 'prioridade_judicial', 'capacidade_legal', 'curatela_decisao_apoiada', 'crimes_contra_pcd', 'protecao_social', 'politica_nacional_cuidados', 'meia_entrada', 'acessibilidade_arquitetonica', 'acessibilidade_digital', 'esporte_paralimpico'],
        },
    ];

    function getTrilhaId(catId) {
        for (const t of TRILHAS) {
            if (t.ids && t.ids.includes(catId)) return t.id;
        }
        return 'cidadania';
    }

    function renderTrilhaTabs() {
        if (!dom.trilhaTabs || !direitosData) return;
        const counts = {};
        for (const t of TRILHAS) {
            counts[t.id] = t.ids ? direitosData.filter((c) => t.ids.includes(c.id)).length : direitosData.length;
        }
        dom.trilhaTabs.innerHTML = TRILHAS
            .map((t, i) => `
<button type="button" class="trilha-tab" role="tab"
id="trilhaTab-${t.id}"
aria-selected="${i === 0 ? 'true' : 'false'}"
aria-controls="categoryGrid"
data-trilha="${t.id}"
tabindex="${i === 0 ? '0' : '-1'}">
<span class="trilha-tab__label">${escapeHtml(t.label)}</span>
<span class="trilha-tab__count" aria-label="${counts[t.id]} direitos">${counts[t.id]}</span>
</button>`)
            .join('');

        const tabs = dom.trilhaTabs.querySelectorAll('.trilha-tab');
        tabs.forEach((tab) => {
            tab.addEventListener('click', () => selectTrilha(tab.dataset.trilha, { scrollIntoView: true }));
            tab.addEventListener('keydown', (e) => {
                if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft' && e.key !== 'Home' && e.key !== 'End') return;
                e.preventDefault();
                const arr = Array.from(tabs);
                const idx = arr.indexOf(tab);
                let next = idx;
                if (e.key === 'ArrowRight') next = (idx + 1) % arr.length;
                else if (e.key === 'ArrowLeft') next = (idx - 1 + arr.length) % arr.length;
                else if (e.key === 'Home') next = 0;
                else if (e.key === 'End') next = arr.length - 1;
                arr[next].focus();
                selectTrilha(arr[next].dataset.trilha, { scrollIntoView: true });
            });
        });

        // Default = primeira trilha ('todas'). Mostra as 42 categorias e os
        // botões por área funcionam como filtro visível. Resolve a confusão
        // de filtro silencioso onde o usuário não percebia que os botões
        // eram filtros.
        selectTrilha(TRILHAS[0].id);
    }

    function selectTrilha(trilhaId, opts = {}) {
        if (!dom.trilhaTabs || !dom.categoryGrid) return;
        dom.trilhaTabs.querySelectorAll('.trilha-tab').forEach((tab) => {
            const active = tab.dataset.trilha === trilhaId;
            tab.setAttribute('aria-selected', active ? 'true' : 'false');
            tab.setAttribute('tabindex', active ? '0' : '-1');
        });
        dom.categoryGrid.setAttribute('aria-labelledby', `trilhaTab-${trilhaId}`);
        // Pinta os cards conforme trilha selecionada via data-active-trilha
        // (CSS aplica cor de destaque por trilha). 'todas' não pinta — visual
        // neutro para evitar arco-íris de 42 cards.
        if (trilhaId === 'todas') {
            dom.categoryGrid.removeAttribute('data-active-trilha');
        } else {
            dom.categoryGrid.setAttribute('data-active-trilha', trilhaId);
        }
        dom.categoryGrid.querySelectorAll('.category-card').forEach((card) => {
            const show = trilhaId === 'todas' || card.dataset.trilha === trilhaId;
            card.style.display = show ? '' : 'none';
        });
        // UX: ao clicar num filtro, rola o grid para o topo da viewport
        // (abaixo do header sticky ~80px) para que os cards filtrados sejam
        // imediatamente visíveis. Sem isso, com 7 trilha-tabs ocupando ~140px,
        // os cards ficam fora da viewport e o usuário não vê feedback do filtro.
        if (opts.scrollIntoView) {
            const rect = dom.categoryGrid.getBoundingClientRect();
            const targetY = window.scrollY + rect.top - 80;
            const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            window.scrollTo({ top: targetY, behavior: reduceMotion ? 'auto' : 'smooth' });
        }
    }

    function getPendingLegalReviews(catId) {
        if (!catId || !legalReviewByCategory) return [];
        return legalReviewByCategory[catId] || [];
    }

    function renderLegalReviewNotice(cat) {
        const reviews = getPendingLegalReviews(cat && cat.id);
        if (!reviews.length) return '';
        const refs = reviews.map((r) => {
            if (r.issue_url && isSafeUrl(r.issue_url)) {
                return `<li><strong>${escapeHtml(r.titulo)}</strong>: ${escapeHtml(r.aviso_curto)} <a href="${escapeHtml(r.issue_url)}" target="_blank" rel="noopener noreferrer">(Issue #${escapeHtml(String(r.issue || ''))})</a></li>`;
            }
            return `<li><strong>${escapeHtml(r.titulo)}</strong>: ${escapeHtml(r.aviso_curto)}</li>`;
        }).join('');
        return `<aside class="aviso-revisao-juridica" role="note" aria-label="Aviso de revisão jurídica pendente">
<p><strong>⚖️ Conteúdo com revisão jurídica humana pendente.</strong></p>
<ul>${refs}</ul>
<p>Nota do sistema: esta informação é educacional e não substitui orientação profissional.</p>
</aside>`;
    }

    function renderSearchLegalReviewBanner(scored) {
        if (!Array.isArray(scored) || scored.length === 0) return '';
        const seen = new Set();
        const flaggedTitles = [];
        scored.forEach(({ cat }) => {
            getPendingLegalReviews(cat.id).forEach((review) => {
                const key = review.id || `${review.titulo}:${review.aviso_curto}`;
                if (!seen.has(key)) {
                    seen.add(key);
                    flaggedTitles.push(review.titulo);
                }
            });
        });
        if (!flaggedTitles.length) return '';
        return `<div class="search-suggestion search-review-warning" role="note">
<p><strong>⚖️ Atenção:</strong> esta busca retornou conteúdo com validação jurídica humana pendente. Confira as fontes oficiais e, se necessário, busque Defensoria/advogado.</p>
</div>`;
    }

    /**
     * Renderiza uma linha de atribuição editorial reforçando que o bloco
     * (dicas, passo-a-passo) é uma reprodução de fonte oficial — não opinião.
     * Usa a primeira base_legal como fonte primária; cai em texto genérico se ausente.
     * @param {object} cat       direito atual
     * @param {string} blocoNome label curto do bloco (ex.: 'dicas', 'passo-a-passo')
     * @returns {string} HTML seguro (sem dependência de innerHTML externa)
     */
    function renderAtribuicao(cat, blocoNome) {
        const primaria = cat.base_legal && cat.base_legal[0];
        const dataStr = cat.data_ultima_verificacao
            ? new Date(cat.data_ultima_verificacao + 'T00:00:00Z').toLocaleDateString('pt-BR')
            : 'data não informada';
        if (primaria && primaria.lei) {
            return `<p class="atribuicao-fonte"><small><strong>Reproduzido de:</strong> ${escapeHtml(primaria.lei)}${primaria.artigo ? ' — ' + escapeHtml(primaria.artigo) : ''}. Última consulta: ${escapeHtml(dataStr)}.</small></p>`;
        }
        return `<p class="atribuicao-fonte"><small><strong>Reproduzido das fontes oficiais</strong> listadas em "Base Legal" e "Fonte oficial deste conteúdo". Última consulta: ${escapeHtml(dataStr)}.</small></p>`;
    }

    /**
     * G4 — classifica um URL e devolve um badge curto + tooltip indicando
     * a natureza da fonte (governo BR, judiciário, OMS, etc.).
     * Domínios sincronizados com data/fontes_oficiais.json.
     * @param {string} url URL absoluta
     * @returns {string} HTML do badge (vazio se host não-allowlisted — não deveria acontecer
     *                   porque G1 impede isso, mas é defensivo)
     */
    function renderFonteBadge(url) {
        if (!url || typeof url !== 'string') return '';
        let host;
        try { host = new URL(url).hostname.toLowerCase(); } catch { return ''; }
        const matches = [
            { re: /\.planalto\.gov\.br$/, label: '✓ fonte oficial', title: 'Planalto — legislação federal' },
            { re: /\.in\.gov\.br$/, label: '✓ fonte oficial', title: 'Imprensa Nacional — Diário Oficial' },
            { re: /\.jus\.br$/, label: '✓ fonte oficial', title: 'Poder Judiciário brasileiro' },
            { re: /\.def\.br$/, label: '✓ fonte oficial', title: 'Defensoria Pública' },
            { re: /\.leg\.br$/, label: '✓ fonte oficial', title: 'Poder Legislativo brasileiro' },
            { re: /\.mp\.br$/, label: '✓ fonte oficial', title: 'Ministério Público' },
            { re: /\.mil\.br$/, label: '✓ fonte oficial', title: 'Forças Armadas brasileiras' },
            { re: /icd\.who\.int$|^www\.who\.int$/, label: '✓ fonte OMS', title: 'Organização Mundial da Saúde (adotada pelo Ministério da Saúde — Portaria GM/MS 1.405/2022)' },
            { re: /\.gov\.br$/, label: '✓ fonte oficial', title: 'Governo brasileiro (.gov.br)' },
        ];
        for (const m of matches) {
            if (m.re.test(host)) {
                return ` <span class="fonte-badge" title="${escapeHtml(m.title)}">${escapeHtml(m.label)}</span>`;
            }
        }
        return '';
    }

    function showDetalhe(id, skipHistory) {
        const cat = direitosData && direitosData.find((c) => c.id === id);
        if (!cat || !dom.categoriasSection || !dom.detalheSection) return;
        dom.categoriasSection.style.display = 'none';
        dom.detalheSection.style.display = '';
        updateSectionAlternation();
        if (!skipHistory) {
            history.pushState({ view: 'detalhe', id }, '', `#direito/${id}`);
        }
        let html = `
<article>
<h2>${escapeHtml(cat.titulo)}</h2>
<p class="detalhe-resumo">${escapeHtml(cat.resumo)}</p>
<aside class="banner-glossario" role="note" aria-label="Sobre este conteúdo">
<p><strong>Catálogo público de direitos PcD.</strong> Esta página <em>reúne referências</em> a fontes oficiais brasileiras (.gov.br, .jus.br, .def.br, .leg.br, .mp.br) e à Organização Mundial da Saúde (icd.who.int — adotada pelo Ministério da Saúde) listadas abaixo. <strong>Não verificamos em tempo real, não interpretamos a lei, não orientamos casos individuais.</strong> Confirme sempre na fonte oficial linkada.</p>
</aside>`;
        if (cat.data_ultima_verificacao) {
            const STALENESS_DAYS = 180;
            const verifDate = new Date(cat.data_ultima_verificacao + 'T00:00:00Z');
            if (!isNaN(verifDate.getTime())) {
                const ageDays = Math.floor((Date.now() - verifDate.getTime()) / 86400000);
                if (ageDays > STALENESS_DAYS) {
                    html += `<aside class="aviso-staleness" role="note" aria-label="Aviso de conteúdo desatualizado">
<p><strong>⚠️ Conteúdo verificado há mais de ${STALENESS_DAYS} dias (${ageDays} dias atrás).</strong></p>
<p>A legislação pode ter mudado. Confirme a regra atual na <a href="https://www.gov.br/" target="_blank" rel="noopener noreferrer">fonte oficial</a> antes de agir e considere relatar o problema em <a href="https://github.com/fabiotreze/nossodireito/issues" target="_blank" rel="noopener noreferrer">issues do repositório</a>.</p>
</aside>`;
                }
            }
        }
        html += renderLegalReviewNotice(cat);
        if (cat.requer_consulta_especializada === true) {
            html += `<aside class="aviso-consulta-juridica" role="note" aria-label="Aviso de orientação jurídica especializada">
<p><strong>ℹ️ Este direito costuma exigir orientação jurídica especializada.</strong></p>
<p>Envolve perícia, prazos ou recursos. A <a href="https://www.defensoria.gov.br/" target="_blank" rel="noopener noreferrer">Defensoria Pública</a> oferece atendimento gratuito; também é possível consultar um(a) advogado(a) de sua confiança.</p>
</aside>`;
        }
        if (cat.valor) {
            html += `<div class="detalhe-section">
<h3>Valor citado pela fonte oficial</h3>
<span class="valor-destaque">${escapeHtml(cat.valor)}</span>
<p class="valor-aviso"><small><strong>⚠️ Atenção:</strong> valor publicado em fonte oficial — pode ter sido reajustado. Confirme na fonte linkada em "Base Legal" antes de tomar decisões.</small></p>
</div>`;
        }
        if (cat.base_legal && cat.base_legal.length) {
            html += `<div class="detalhe-section">
<h3>Base Legal</h3>
<div>${cat.base_legal
                    .map(
                        (l) =>
                            `<a class="legal-link" href="${escapeHtml(l.link)}" target="_blank" rel="noopener noreferrer">
${escapeHtml(l.lei)}${l.artigo ? ' — ' + escapeHtml(l.artigo) : ''}
</a>${renderFonteBadge(l.link)}`
                    )
                    .join('')}</div>
</div>`;
        }
        if (cat.requisitos && cat.requisitos.length) {
            html += `<div class="detalhe-section">
<h3>Requisitos</h3>
${renderAtribuicao(cat, 'requisitos')}
<ul>${cat.requisitos.map((r) => `<li>${escapeHtml(r)}</li>`).join('')}</ul>
</div>`;
        }
        if (cat.documentos && cat.documentos.length) {
            html += `<div class="detalhe-section">
<h3>Documentos Necessários</h3>
${renderAtribuicao(cat, 'documentos')}
<ul>${cat.documentos.map((d) => `<li>${escapeHtml(d)}</li>`).join('')}</ul>
</div>`;
        }
        if (cat.passo_a_passo && cat.passo_a_passo.length) {
            const passosHtml = `<ol>${cat.passo_a_passo.map((p) => `<li>${escapeHtml(p)}</li>`).join('')}</ol>`;
            const atribuicaoPasso = renderAtribuicao(cat, 'passo-a-passo');
            const procedimentoAviso = `<p class="procedimento-aviso"><small><strong>⚠️ Atenção:</strong> este é o <strong>procedimento descrito pela fonte oficial</strong> linkada abaixo. NossoDireito apenas reproduz — não orienta seu caso. Confirme na fonte oficial antes de seguir qualquer etapa.</small></p>`;
            if (cat.requer_consulta_especializada === true) {
                // Atrito inline (não-bloqueante): leitor abre deliberadamente após ver aviso jurídico
                html += `<div class="detalhe-section">
<details class="passo-a-passo-atrito">
<summary><h3 style="display:inline">Procedimento descrito pela fonte oficial</h3> <span class="atrito-hint">(clique para abrir — ler aviso acima primeiro)</span></summary>
${atribuicaoPasso}
${procedimentoAviso}
${passosHtml}
</details>
</div>`;
            } else {
                html += `<div class="detalhe-section">
<h3>Procedimento descrito pela fonte oficial</h3>
${atribuicaoPasso}
${procedimentoAviso}
${passosHtml}
</div>`;
            }
        }
        if (cat.onde) {
            const canal = cat.canal_de_atendimento_oficial || cat.onde;
            html += `<div class="detalhe-section">
<h3>Fonte oficial deste conteúdo</h3>
<p>${escapeHtml(canal)}</p>
<p class="canal-aviso"><small>O NossoDireito apenas reproduz o que essa fonte publicou. O direito é peticionado/concedido somente pelo canal acima — este site não tem competência legal nem administrativa.</small></p>
</div>`;
        }
        if (cat.dicas && cat.dicas.length) {
            const DICAS_LIMIT = 5;
            const visibleDicas = cat.dicas.slice(0, DICAS_LIMIT);
            const hiddenDicas = cat.dicas.slice(DICAS_LIMIT);
            html += `<div class="detalhe-section">
<h3>Observações citadas pela fonte oficial</h3>
${renderAtribuicao(cat, 'observações')}
<p class="observacoes-aviso"><small><strong>⚠️ Atenção:</strong> trechos reproduzidos da fonte oficial. NossoDireito não opina, não orienta e não garante aplicabilidade ao seu caso.</small></p>
${visibleDicas.map((d) => `<div class="dica-item">${escapeHtml(d)}</div>`).join('')}
${hiddenDicas.length ? `<div class="dicas-hidden" id="dicasHidden_${cat.id}" style="display:none">${hiddenDicas.map((d) => `<div class="dica-item">${escapeHtml(d)}</div>`).join('')}</div>
<button type="button" class="btn-ver-mais" id="dicasToggle_${cat.id}" aria-expanded="false" aria-controls="dicasHidden_${cat.id}">Mostrar mais ${hiddenDicas.length} observação${hiddenDicas.length > 1 ? 'es' : ''} ▼</button>` : ''}
</div>`;
        }
        if (cat.ipva_estados && cat.ipva_estados.length) {
            html += `<div class="detalhe-section"><h3>Isenção de IPVA por Estado</h3>
<details><summary>Ver legislação dos ${cat.ipva_estados.length} estados</summary>
<div class="table-wrapper"><table class="ipva-table">
<thead><tr><th>UF</th><th>Lei</th><th>Art.</th><th>SEFAZ</th></tr></thead>
<tbody>${cat.ipva_estados.map(e => `<tr><td>${escapeHtml(e.uf)}</td><td>${escapeHtml(e.lei)}</td><td>${escapeHtml(e.art)}</td><td><a href="${escapeHtml(e.sefaz)}" target="_blank" rel="noopener noreferrer">Consultar</a></td></tr>`).join('')}</tbody>
</table></div></details></div>`;
        }
        if (cat.ipva_estados_detalhado && cat.ipva_estados_detalhado.length) {
            html += `<div class="detalhe-section">
<h3>Consulta Detalhada — IPVA por Estado</h3>
<p style="margin-bottom:12px;color:var(--text-muted)">
Selecione seu estado para ver as condições específicas, limites de valor e legislação completa:
</p>
<label for="ipvaEstadoSelect" class="sr-only">Selecione seu estado</label>
<select id="ipvaEstadoSelect" class="ipva-dropdown">
<option value="">Selecione seu estado...</option>
${cat.ipva_estados_detalhado.map(e =>
                `<option value="${escapeHtml(e.uf)}">${escapeHtml(e.uf)} - ${escapeHtml(e.nome)}</option>`
            ).join('')}
</select>
<div id="ipvaEstadoInfo" class="ipva-info-box" role="region" aria-live="polite"></div>
</div>`;
        }
        if (cat.links && cat.links.length) {
            html += `<div class="detalhe-section">
<h3>Links Úteis</h3>
<div>${cat.links
                    .filter((l) => isSafeUrl(l.url))
                    .map(
                        (l) =>
                            `<a class="legal-link" href="${escapeHtml(l.url)}" target="_blank" rel="noopener noreferrer">
${escapeHtml(l.titulo)}
</a>`
                    )
                    .join('')}</div>
</div>`;
        }
        if (cat.govbr_servico_id) {
            const live = sessionStorage.getItem('govbr_' + cat.govbr_servico_id);
            const govbrUrl = cat.govbr_url || `https://www.gov.br/pt-br/servicos/${cat.govbr_servico_id}`;
            html += `<div class="detalhe-section" style="text-align:center">
<a href="${escapeHtml(govbrUrl)}" target="_blank" rel="noopener noreferrer" class="btn-govbr${live ? ' live' : ''}">
${live ? 'Serviço digital confirmado no gov.br' : 'Acessar serviço no gov.br'}
</a></div>`;
        }
        if (cat.tags && cat.tags.length) {
            html += `<div class="detalhe-tags">
${cat.tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
</div>`;
        }
        const shareText = encodeURIComponent(
            `${cat.titulo}\n${cat.resumo}\n\nVeja mais em: https://nossodireito.fabiotreze.com`
        );
        html += `<div class="detalhe-section" style="text-align:center;padding-top:8px;">
<div style="display:inline-flex;gap:8px;">
<a href="https://wa.me/?text=${shareText}" target="_blank" rel="noopener noreferrer"
class="btn btn-sm btn-whatsapp" aria-label="Compartilhar no WhatsApp">
WhatsApp
</a>
<button id="exportDetalhePdf" class="btn btn-sm btn-outline" type="button" aria-label="Salvar direito como PDF">
Salvar PDF
</button>
</div>
</div>`;
        if (cat.data_ultima_verificacao) {
            const d = cat.data_ultima_verificacao;
            const m = d.match(/^(\d{4})-(\d{2})-(\d{2})$/);
            const dataFmt = m ? `${m[3]}/${m[2]}/${m[1]}` : d;
            html += `<p class="detalhe-verificacao"><small>✓ Conteúdo verificado em <time datetime="${escapeHtml(d)}">${escapeHtml(dataFmt)}</time>. Sempre confirme com a fonte oficial antes de agir.</small></p>`;
        }
        // M6: botão "Sugerir correção" → pré-preenche issue template "correcao.yml" via querystring
        const correcaoUrl = `https://github.com/fabiotreze/nossodireito/issues/new?template=correcao.yml&direito_id=${encodeURIComponent(cat.id)}&title=${encodeURIComponent('[correção] ' + cat.titulo)}`;
        html += `<p class="detalhe-sugerir-correcao"><a href="${correcaoUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline" aria-label="Sugerir correção para este direito">Sugerir correção</a></p>`;
        html += `</article>`;
        dom.detalheContent.innerHTML = html;
        const exportDetalheBtn = document.getElementById('exportDetalhePdf');
        if (exportDetalheBtn) {
            exportDetalheBtn.addEventListener('click', () => {
                const detalheSection = document.querySelector('#detalhe');
                if (detalheSection) {
                    detalheSection.setAttribute('data-print-date', new Date().toLocaleDateString('pt-BR'));
                    detalheSection.setAttribute('data-print-title', cat.titulo);
                }
                document.body.classList.add('printing-detalhe');
                window.print();
                const cleanup = () => {
                    document.body.classList.remove('printing-detalhe');
                    window.removeEventListener('afterprint', cleanup);
                };
                window.addEventListener('afterprint', cleanup);
                setTimeout(cleanup, 5000);
            });
        }
        /* Toggle "Mostrar mais" dicas */
        const dicasToggle = document.getElementById(`dicasToggle_${cat.id}`);
        if (dicasToggle) {
            dicasToggle.addEventListener('click', () => {
                const hidden = document.getElementById(`dicasHidden_${cat.id}`);
                if (!hidden) return;
                const expanded = dicasToggle.getAttribute('aria-expanded') === 'true';
                hidden.style.display = expanded ? 'none' : 'block';
                dicasToggle.setAttribute('aria-expanded', String(!expanded));
                dicasToggle.textContent = expanded
                    ? `Mostrar mais ${hidden.children.length} dica${hidden.children.length > 1 ? 's' : ''} ▼`
                    : 'Mostrar menos ▲';
            });
        }
        if (cat.ipva_estados_detalhado && cat.ipva_estados_detalhado.length) {
            const ipvaSelect = $('#ipvaEstadoSelect');
            const ipvaInfo = $('#ipvaEstadoInfo');
            if (ipvaSelect && ipvaInfo) {
                ipvaSelect.addEventListener('change', function (e) {
                    const uf = e.target.value;
                    if (!uf) {
                        ipvaInfo.innerHTML = '';
                        return;
                    }
                    const estado = cat.ipva_estados_detalhado.find(item => item.uf === uf);
                    if (estado) {
                        ipvaInfo.innerHTML = `
<div class="ipva-detail-card">
<h4>${escapeHtml(estado.nome)} (${escapeHtml(estado.uf)})</h4>
<div class="ipva-detail-row">
<strong>Legislação:</strong>
<span>${escapeHtml(estado.lei)}</span>
</div>
<div class="ipva-detail-row">
<strong>Artigo:</strong>
<span>${escapeHtml(estado.artigo)}</span>
</div>
<div class="ipva-detail-row">
<strong>Condições para isenção:</strong>
<span>${escapeHtml(estado.condicoes)}</span>
</div>
<div class="ipva-detail-row">
<strong>Limite de valor:</strong>
<span>${escapeHtml(estado.limite_valor)}</span>
</div>
<a href="${escapeHtml(estado.sefaz)}"
target="_blank"
rel="noopener noreferrer"
class="btn btn-primary"
style="margin-top:16px;display:inline-block">
🔗 Consultar na SEFAZ/${escapeHtml(estado.uf)}
</a>
</div>
`;
                    }
                });
            }
        }
        // v1.43.12: scroll para a seção #detalhe (não para o topo absoluto da
        // página). v1.43.5 introduziu um window.scrollTo({top:0}) que sobrescrevia
        // o scrollIntoView e levava o usuário ao hero ao abrir um direito.
        const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        dom.detalheSection.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
        const h2 = dom.detalheSection.querySelector('h2');
        if (h2) { h2.setAttribute('tabindex', '-1'); h2.focus({ preventScroll: true }); }
    }
    function setupSearch() {
        if (!dom.searchInput || !dom.searchResults || !dom.searchBtn) return;
        const doSearch = () => {
            const query = dom.searchInput.value.trim().toLowerCase();
            if (!query || !direitosData) {
                dom.searchResults.innerHTML = '';
                return;
            }
            performSearch(query);
        };
        dom.searchBtn.addEventListener('click', doSearch);
        dom.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); doSearch(); }
        });
        // Chromium fires a native 'search' event on Enter for <input type="search">,
        // which clears the field.  Intercept to prevent clear and double-trigger.
        dom.searchInput.addEventListener('search', (e) => { e.preventDefault(); });
        let timer;
        dom.searchInput.addEventListener('input', () => {
            clearTimeout(timer);
            timer = setTimeout(doSearch, 300);
        });
    }
    function levenshtein(a, b) {
        if (a.length === 0) return b.length;
        if (b.length === 0) return a.length;
        // Two-row optimization: O(min(m,n)) space instead of O(m*n)
        if (a.length < b.length) { const t = a; a = b; b = t; }
        let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
        let curr = new Array(b.length + 1);
        for (let i = 1; i <= a.length; i++) {
            curr[0] = i;
            for (let j = 1; j <= b.length; j++) {
                const cost = a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1;
                curr[j] = Math.min(
                    prev[j] + 1,
                    curr[j - 1] + 1,
                    prev[j - 1] + cost
                );
            }
            [prev, curr] = [curr, prev];
        }
        return prev[b.length];
    }
    let _cachedDictionary = null;
    function buildSearchDictionary() {
        if (_cachedDictionary) return _cachedDictionary;
        const words = new Set();
        Object.keys(KEYWORD_MAP).forEach((k) => {
            normalizeText(k).split(/\s+/).forEach((w) => { if (w.length > 2) words.add(w); });
        });
        if (direitosData) {
            direitosData.forEach((cat) => {
                const text = [cat.titulo, cat.resumo, ...(cat.tags || [])].join(' ');
                normalizeText(text).split(/\s+/).forEach((w) => { if (w.length > 2) words.add(w); });
            });
        }
        _cachedDictionary = Array.from(words);
        return _cachedDictionary;
    }
    function findClosestWord(term, dictionary, maxDist) {
        let best = null;
        let bestDist = maxDist + 1;
        for (const word of dictionary) {
            if (Math.abs(word.length - term.length) > maxDist) continue;
            const d = levenshtein(term, word);
            if (d < bestDist) {
                bestDist = d;
                best = word;
                if (d === 1) break;
            }
        }
        return bestDist <= maxDist ? best : null;
    }
    const ESTADOS_BR = {
        'acre': 'AC', 'alagoas': 'AL', 'amapa': 'AP', 'amazonas': 'AM', 'bahia': 'BA',
        'ceara': 'CE', 'distrito federal': 'DF', 'espirito santo': 'ES', 'goias': 'GO',
        'maranhao': 'MA', 'mato grosso': 'MT', 'mato grosso do sul': 'MS', 'minas gerais': 'MG',
        'para': 'PA', 'paraiba': 'PB', 'parana': 'PR', 'pernambuco': 'PE', 'piaui': 'PI',
        'rio de janeiro': 'RJ', 'rio grande do norte': 'RN', 'rio grande do sul': 'RS',
        'rondonia': 'RO', 'roraima': 'RR', 'santa catarina': 'SC', 'sao paulo': 'SP',
        'sergipe': 'SE', 'tocantins': 'TO',
    };
    const UF_SET = new Set(Object.values(ESTADOS_BR));
    // Normalize geo input the same way scripts/build_municipios.py builds the `k`
    // field of data/municipios_br.json: NFD-strip accents, lowercase, drop
    // apostrophes/hyphens/dots, collapse whitespace. Keeps detection consistent
    // with the IBGE snapshot.
    function _normalizeGeo(s) {
        if (!s) return '';
        return String(s)
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase()
            .replace(/['\-.]/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    }
    // Title-case a normalized geo name for display ("sao paulo" → "São Paulo" is
    // not possible without the original; we just capitalize words and let the
    // município `n` field carry true casing when we have an IBGE hit).
    function _titleCaseGeo(s) {
        return String(s).split(' ').map((w) => w ? w[0].toUpperCase() + w.slice(1) : '').join(' ');
    }
    function detectLocation(queryNorm) {
        const qRaw = String(queryNorm || '').trim();
        if (!qRaw) return null;
        // 1. UF sigla (exact, case-insensitive, 2 chars)
        if (qRaw.length === 2 && UF_SET.has(qRaw.toUpperCase())) {
            const uf = qRaw.toUpperCase();
            return { type: 'uf', uf, name: uf, matched: qRaw.toLowerCase(), ibge_id: null };
        }
        const q = _normalizeGeo(qRaw);
        if (!q) return null;
        const estadoUF = ESTADOS_BR[q] || null;
        const muniHit = municipiosByKey && municipiosByKey.has(q) ? municipiosByKey.get(q) : null;
        // 2. Resolução exata (município vs. estado, com tie-break por UF).
        //    Se o nome bate tanto em estado quanto em município, o município
        //    só vence quando ambos apontam para a mesma UF — assim "São Paulo"
        //    e "Rio de Janeiro" viram capital (mais útil), enquanto pequenos
        //    municípios homônimos a estados ("Espírito Santo" em RN) não
        //    sequestram a UF que o usuário provavelmente quer.
        if (muniHit && (!estadoUF || muniHit.u === estadoUF)) {
            return { type: 'cidade', uf: muniHit.u, name: muniHit.n, matched: muniHit.k, ibge_id: muniHit.id };
        }
        if (estadoUF) {
            return { type: 'estado', uf: estadoUF, name: q, matched: q, ibge_id: null };
        }
        // 3. Município por substring com fronteira de palavra (escolhe o mais
        //    longo para evitar "São Paulo" engolir "São Paulo do Potengi").
        if (municipiosData && municipiosData.length) {
            const padded = ' ' + q + ' ';
            let best = null;
            for (let i = 0; i < municipiosData.length; i++) {
                const m = municipiosData[i];
                if (padded.indexOf(' ' + m.k + ' ') !== -1) {
                    if (!best || m.k.length > best.k.length) best = m;
                }
            }
            if (best) {
                return { type: 'cidade', uf: best.u, name: best.n, matched: best.k, ibge_id: best.id };
            }
        }
        // 4. Estado por substring (fallback)
        for (const estado in ESTADOS_BR) {
            if ((' ' + q + ' ').indexOf(' ' + estado + ' ') !== -1) {
                return { type: 'estado', uf: ESTADOS_BR[estado], name: estado, matched: estado, ibge_id: null };
            }
        }
        return null;
    }
    function renderLocationResults(location, query, filteredCats) {
        const ufLabel = location.uf;
        const nomeDisplay = location.type === 'uf'
            ? location.name
            : (location.type === 'cidade' ? location.name : _titleCaseGeo(location.name));
        const orgao = orgaosEstaduaisData
            ? orgaosEstaduaisData.find((o) => o.uf === ufLabel)
            : null;
        const cats = filteredCats || direitosData
            .map((cat) => ({ cat, score: 1 }))
            .sort((a, b) => a.cat.titulo.localeCompare(b.cat.titulo));
        const orgaoHtml = orgao && isSafeUrl(orgao.url)
            ? `<p class="search-orgao">Órgão estadual (${escapeHtml(ufLabel)}): <a href="${escapeHtml(orgao.url)}" target="_blank" rel="noopener noreferrer"><strong>${escapeHtml(orgao.nome)}</strong> ↗</a></p>`
            : orgao
                ? `<p class="search-orgao">Órgão estadual (${escapeHtml(ufLabel)}): <strong>${escapeHtml(orgao.nome)}</strong></p>`
                : '';
        /* ── Portais estaduais (SEFAZ / DETRAN) ── */
        let portaisHtml = '';
        if (orgao && (orgao.sefaz || orgao.detran)) {
            const links = [];
            if (orgao.sefaz && isSafeUrl(orgao.sefaz))
                links.push(`<a href="${escapeHtml(orgao.sefaz)}" target="_blank" rel="noopener noreferrer" class="legal-link">SEFAZ/${escapeHtml(ufLabel)}</a>`);
            if (orgao.detran && isSafeUrl(orgao.detran))
                links.push(`<a href="${escapeHtml(orgao.detran)}" target="_blank" rel="noopener noreferrer" class="legal-link">DETRAN/${escapeHtml(ufLabel)}</a>`);
            portaisHtml = `<div class="search-portais" style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;">${links.join('')}</div>`;
        }
        /* ── Benefícios destaque estaduais ── */
        let beneficiosHtml = '';
        if (orgao && orgao.beneficios_destaque && orgao.beneficios_destaque.length) {
            beneficiosHtml = `<details class="search-beneficios-estado" style="margin:8px 0;">
<summary style="cursor:pointer;font-weight:600;">Benefícios específicos — ${escapeHtml(ufLabel)}</summary>
<ul style="margin:8px 0 0 16px;padding:0;list-style:none;">
${orgao.beneficios_destaque.map(b => `<li style="padding:4px 0;">${escapeHtml(b)}</li>`).join('')}
</ul>
</details>`;
        }
        const filterNote = filteredCats
            ? `<p class="search-hint">Mostrando <strong>${filteredCats.length}</strong> resultado(s) filtrado(s) para sua busca em <strong>${escapeHtml(nomeDisplay)}</strong>.</p>`
            : '';
        // Aviso honesto: identificamos o município pelo IBGE, mas ainda não
        // temos curadoria de órgãos municipais (prefeituras). Os direitos
        // federais valem; o estadual aparece via SEFAZ/DETRAN acima.
        const municipalNote = location.type === 'cidade'
            ? `<p class="search-hint" style="color:var(--text-muted);font-style:italic;">Ainda não temos dados específicos da prefeitura de <strong>${escapeHtml(nomeDisplay)}</strong>. Os direitos federais valem aqui; consulte também os portais estaduais (${escapeHtml(ufLabel)}) acima.</p>`
            : '';
        dom.searchResults.innerHTML =
            `<div class="search-suggestion search-location">
<p><strong>${escapeHtml(nomeDisplay)}</strong> ${location.type === 'cidade' ? `(${escapeHtml(ufLabel)})` : ''} — os direitos abaixo são <strong>federais</strong> e valem em todo o Brasil, incluindo na sua cidade/estado.</p>
${orgaoHtml}
${portaisHtml}
${beneficiosHtml}
${municipalNote}
${filterNote}
<p class="search-hint">Clique em qualquer direito para ver detalhes, documentos e passo a passo.</p>
</div>` +
            renderSearchResults(cats, { showReviewBanner: Boolean(filteredCats) });
        bindSearchResultEvents();
    }
    // Stopwords PT-BR: common words that add no search value
    const STOPWORDS = new Set([
        'e', 'ou', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas',
        'para', 'por', 'com', 'sem', 'que', 'o', 'a', 'os', 'as', 'um', 'uma',
        'uns', 'umas', 'ao', 'aos', 'seu', 'sua', 'meu', 'minha', 'ele', 'ela',
        'se', 'como', 'mais', 'mas', 'muito', 'tambem', 'ja', 'ate', 'sobre',
        'entre', 'tem', 'ter', 'esta', 'esse', 'essa', 'isso', 'isto',
    ]);
    function performSearch(query) {
        const raw = query
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/[,;.!?()]/g, ' ')   // strip punctuation
            .split(/\s+/)
            .filter(Boolean);
        // Keep stopwords for phrase matching / location detection but filter for scoring
        const terms = raw.filter((t) => !STOPWORDS.has(t.toLowerCase()));
        const queryNorm = raw.join(' ');
        const location = detectLocation(queryNorm);
        if (location) {
            // Extract non-location terms for combined search (e.g. "TEA Barueri")
            const locWords = location.matched.split(/\s+/);
            const remainingTerms = terms.filter((t) => !locWords.includes(t.toLowerCase()));
            const remainingRaw = raw.filter((t) => !locWords.includes(t.toLowerCase()));
            if (remainingTerms.length > 0) {
                // Combined search: filter results by remaining terms + show location banner
                const scored = scoreSearch(remainingTerms, remainingRaw);
                if (scored.length > 0) {
                    renderLocationResults(location, query, scored);
                    return;
                }
            }
            renderLocationResults(location, query, null);
            return;
        }
        const scored = scoreSearch(terms, raw);
        if (scored.length === 0 && terms.some((t) => t.length > 3)) {
            const dictionary = buildSearchDictionary();
            const corrected = terms.map((t) => {
                if (t.length <= 3) return t;
                const closest = findClosestWord(t, dictionary, 2);
                return closest || t;
            });
            const correctedQuery = corrected.join(' ');
            if (correctedQuery !== terms.join(' ')) {
                const rescored = scoreSearch(corrected, corrected);
                if (rescored.length > 0) {
                    dom.searchResults.innerHTML =
                        `<div class="search-suggestion"><p>Mostrando resultados para "<strong>${escapeHtml(correctedQuery)}</strong>" <span class="search-original">(você pesquisou "${escapeHtml(query)}")</span></p></div>` +
                        renderSearchResults(rescored, { showReviewBanner: true });
                    bindSearchResultEvents();
                    return;
                }
            }
            dom.searchResults.innerHTML = `
<div class="search-no-results">
<p>Nenhum resultado para "<strong>${escapeHtml(query)}</strong>".</p>
<p>Tente palavras como: BPC, sa\u00fade, escola, transporte, trabalho, TEA, IPVA, moradia, CRAS, FGTS, CID, Libras...</p>
</div>`;
            return;
        }
        if (scored.length === 0) {
            dom.searchResults.innerHTML = `
<div class="search-no-results">
<p>Nenhum resultado para "<strong>${escapeHtml(query)}</strong>".</p>
<p>Tente palavras como: BPC, sa\u00fade, escola, transporte, trabalho, TEA, IPVA, moradia, CRAS, FGTS, CID, Libras...</p>
</div>`;
            return;
        }
        dom.searchResults.innerHTML = renderSearchResults(scored, { showReviewBanner: true });
        bindSearchResultEvents();
    }
    function scoreSearch(terms, rawTerms) {
        const queryJoined = terms.join(' ');
        // Use raw terms (with stopwords) for phrase matching so "sindrome de down" matches fully
        const phraseQuery = rawTerms ? rawTerms.join(' ') : queryJoined;
        const kwScores = {};
        if (KEYWORD_MAP && Object.keys(KEYWORD_MAP).length > 0) {
            for (const [keyword, { cats, weight }] of Object.entries(KEYWORD_MAP)) {
                const normKey = normalizeText(keyword);
                const matches = terms.some((t) => normKey.includes(t) || t.includes(normKey))
                    || queryJoined.includes(normKey) || normKey.includes(queryJoined);
                if (matches) {
                    cats.forEach((catId) => {
                        kwScores[catId] = (kwScores[catId] || 0) + weight;
                    });
                }
            }
        }
        // Phrase bonus: if full query (2+ words) matches as compound, boost those results
        const phraseBonus = (rawTerms ? rawTerms.length : terms.length) >= 2
            ? new RegExp(escapeRegex(phraseQuery), 'g') : null;
        // Pre-compile regexes once for all terms
        const termRegexes = terms.map(t => new RegExp(escapeRegex(t), 'g'));
        // Minimum terms matched threshold: if >1 term, require at least 2 terms to match
        const minTermsHit = terms.length >= 2 ? 2 : 1;
        return direitosData
            .map((cat) => {
                const searchable = normalizeText(
                    [
                        cat.titulo,
                        cat.resumo,
                        ...(cat.tags || []),
                        ...(cat.requisitos || []),
                        ...(cat.passo_a_passo || []),
                        ...(cat.dicas || []),
                    ].join(' ')
                );
                let score = 0;
                let termsHit = 0;
                termRegexes.forEach((regex) => {
                    regex.lastIndex = 0;
                    const count = (searchable.match(regex) || []).length;
                    if (count > 0) termsHit++;
                    score += count;
                });
                // Phrase bonus: boost compound matches (e.g. "sindrome de down" as one phrase)
                if (phraseBonus) {
                    phraseBonus.lastIndex = 0;
                    const phraseHits = (searchable.match(phraseBonus) || []).length;
                    score += phraseHits * 5;
                    if (phraseHits > 0) termsHit = terms.length; // phrase match counts as all terms
                }
                score += (kwScores[cat.id] || 0);
                // If keyword_map matched this category, always include it
                if (kwScores[cat.id]) termsHit = Math.max(termsHit, minTermsHit);
                return { cat, score, termsHit };
            })
            .filter((r) => r.score > 0 && r.termsHit >= minTermsHit)
            .sort((a, b) => b.score - a.score);
    }
    function renderSearchResults(scored, options = {}) {
        const showReviewBanner = options.showReviewBanner !== false;
        const reviewBanner = showReviewBanner ? renderSearchLegalReviewBanner(scored) : '';
        const resultsHtml = scored
            .map(
                ({ cat }) => `
<div class="search-result-item" data-id="${cat.id}" tabindex="0" role="button">
<div class="search-result-info">
<h3>${escapeHtml(cat.titulo)}</h3>
<p>${escapeHtml(cat.resumo)}</p>
${getPendingLegalReviews(cat.id).length ? '<span class="search-result-badge search-result-badge--review">Revisão jurídica</span>' : ''}
</div>
</div>`
            )
            .join('');
        return reviewBanner + resultsHtml;
    }
    function bindSearchResultEvents() {
        dom.searchResults.querySelectorAll('.search-result-item').forEach((item) => {
            item.addEventListener('click', () => showDetalhe(item.dataset.id));
            item.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    showDetalhe(item.dataset.id);
                }
            });
        });
    }
    function renderTransparency() {
        if (!fontesData || !jsonMeta) return;
        if (dom.transLastUpdate) {
            dom.transLastUpdate.textContent = formatDate(jsonMeta.ultima_atualizacao);
        }
        if (dom.transVersion) {
            dom.transVersion.textContent = `v${jsonMeta.versao}`;
        }
        const transLastUpdateInline = document.getElementById('transLastUpdateInline');
        if (transLastUpdateInline) {
            transLastUpdateInline.textContent = formatDate(jsonMeta.ultima_atualizacao);
        }
        const transLastUpdateText = document.getElementById('transLastUpdateText');
        if (transLastUpdateText) {
            transLastUpdateText.textContent = formatDate(jsonMeta.ultima_atualizacao);
        }
        // v1.43.22: listas (legislacao/servicos/normativas) removidas da aba Transparência.
        // Conteúdo migrou para a aba 🔗 Sites Oficiais (catálogo público com filtros).
        // Transparência ficou só com governança (metadados + aviso + LGPD + DPO).
    }
    function renderDocsChecklist() {
        if (!docsMestreData || !direitosData || !dom.docsChecklist) return;
        const catNameMap = {};
        direitosData.forEach((c) => {
            catNameMap[c.id] = c.titulo.split('—')[0].trim();
        });
        // Coleta direitos únicos referenciados em documentos_mestre (com contagem)
        const direitoCount = new Map();
        docsMestreData.forEach((doc) => {
            (doc.categorias || []).forEach((cid) => {
                direitoCount.set(cid, (direitoCount.get(cid) || 0) + 1);
            });
        });
        const direitosOrdenados = [...direitoCount.entries()]
            .map(([id, count]) => ({ id, name: catNameMap[id] || id, count }))
            .sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'));

        // Renderiza filtro + lista (estrutura preservada para acessibilidade)
        const filterId = 'docsChecklistFilter';
        const filterHtml = `
<div class="docs-checklist-filter">
<label for="${filterId}" class="docs-checklist-filter-label">Mostrar documentos para:</label>
<select id="${filterId}" class="docs-checklist-filter-select" aria-label="Filtrar documentos por direito">
<option value="__all__">Todos os direitos (${docsMestreData.length} documentos)</option>
${direitosOrdenados.map((d) => `<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)} (${d.count})</option>`).join('')}
</select>
<span class="docs-checklist-count" id="docsChecklistCount" aria-live="polite"></span>
</div>
<div class="docs-checklist-list" id="docsChecklistList"></div>`;
        dom.docsChecklist.innerHTML = filterHtml;
        const listEl = document.getElementById('docsChecklistList');
        const countEl = document.getElementById('docsChecklistCount');
        const selectEl = document.getElementById(filterId);

        function renderItems(filter) {
            const saved = localGet('docs_checklist') || {};
            const filtered = filter === '__all__'
                ? docsMestreData
                : docsMestreData.filter((doc) => (doc.categorias || []).includes(filter));
            if (countEl) {
                countEl.textContent = filter === '__all__'
                    ? ''
                    : `${filtered.length} documento${filtered.length === 1 ? '' : 's'} para este direito`;
            }
            listEl.innerHTML = filtered.map((doc) => {
                const checked = saved[doc.id] ? 'checked' : '';
                const catTags = (doc.categorias || [])
                    .slice(0, 6)
                    .map((cid) => `<span class="doc-cat-tag">${escapeHtml(catNameMap[cid] || cid)}</span>`)
                    .join('');
                const moreTags = (doc.categorias || []).length > 6
                    ? `<span class="doc-cat-tag doc-cat-tag--more" title="${escapeHtml((doc.categorias || []).slice(6).map(c => catNameMap[c] || c).join(', '))}">+${(doc.categorias || []).length - 6}</span>`
                    : '';
                return `
<article class="doc-master-item">
<label class="doc-master-header">
<input type="checkbox" data-doc-id="${doc.id}" ${checked} aria-label="Marcar ${escapeHtml(doc.nome)} como providenciado">
<div class="doc-master-info">
<h4 class="doc-master-name">${escapeHtml(doc.nome)}</h4>
<p class="doc-master-desc">${escapeHtml(doc.descricao)}</p>
</div>
</label>
<div class="doc-master-meta">
<div class="doc-master-categories" aria-label="Direitos que utilizam este documento">${catTags}${moreTags}</div>
${doc.dica ? `<p class="doc-master-dica"><span class="sr-only">Observação:</span> ${escapeHtml(doc.dica)}</p>` : ''}
</div>
</article>`;
            }).join('');
            // Re-attach checkbox handlers em items recém-renderizados
            listEl.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
                cb.addEventListener('change', () => {
                    const state = localGet('docs_checklist') || {};
                    if (cb.checked) {
                        state[cb.dataset.docId] = true;
                    } else {
                        delete state[cb.dataset.docId];
                    }
                    localSet('docs_checklist', state);
                });
            });
        }

        renderItems('__all__');
        if (selectEl) {
            selectEl.addEventListener('change', () => renderItems(selectEl.value));
        }
    }
    function renderInstituicoes() {
        if (!instituicoesData || !direitosData || !dom.instituicoesGrid) return;
        const catNameMap = {};
        direitosData.forEach((c) => {
            catNameMap[c.id] = c.titulo.split('—')[0].trim();
        });
        function renderInstitutions(filter) {
            const filtered = filter === 'todos'
                ? instituicoesData
                : instituicoesData.filter((i) => i.tipo === filter);
            if (filtered.length === 0) {
                dom.instituicoesGrid.innerHTML = '<p style="text-align:center;color:var(--text-muted);">Nenhuma instituição nesta categoria.</p>';
                return;
            }
            dom.instituicoesGrid.innerHTML = filtered
                .map((inst) => {
                    const tipoLabel = inst.tipo === 'governamental' ? 'Governamental' : inst.tipo === 'ong' ? 'ONG' : 'Profissional';
                    const catTags = (inst.categorias || [])
                        .map((cid) => `<span class="inst-cat-tag">${escapeHtml(catNameMap[cid] || cid)}</span>`)
                        .join('');
                    const servicos = (inst.servicos || [])
                        .slice(0, 3)
                        .map((s) => `<li>${escapeHtml(s)}</li>`)
                        .join('');
                    return `
<div class="inst-card" data-tipo="${inst.tipo}">
<div class="inst-header">
<span class="inst-tipo-badge ${inst.tipo}">${tipoLabel}</span>
</div>
<h3 class="inst-nome">${escapeHtml(inst.nome)}</h3>
<p class="inst-desc">${escapeHtml(inst.descricao)}</p>
${servicos ? `<ul class="inst-servicos">${servicos}</ul>` : ''}
<div class="inst-como">${escapeHtml(inst.como_acessar)}</div>
<div class="inst-categories">${catTags}</div>
${isSafeUrl(inst.url) ? `<a href="${escapeHtml(inst.url)}" class="btn btn-sm btn-outline inst-link" target="_blank" rel="noopener noreferrer">
Acessar site ↗
</a>` : ''}
</div>`;
                })
                .join('');
        }
        renderInstitutions('todos');
        document.querySelectorAll('.inst-filter-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.inst-filter-btn').forEach((b) => {
                    b.classList.remove('active');
                    b.setAttribute('aria-pressed', 'false');
                });
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
                renderInstitutions(btn.dataset.filter);
            });
        });
    }
    function renderLinksUteis() {
        if (!fontesData || !direitosData || !dom.linksGrid) return;
        const seen = new Set();
        const links = [];
        // v1.43.22: cat\u00e1logo unificado \u2014 inclui todas as fontes com URL v\u00e1lida
        // (servi\u00e7os, legisla\u00e7\u00e3o, normativas, programas, portais, refer\u00eancias).
        // Filtro de seguran\u00e7a: isSafeUrl j\u00e1 \u00e9 aplicado depois no render.
        fontesData
            .filter((f) => typeof f.url === 'string' && f.url.length > 0)
            .forEach((f) => {
                if (!seen.has(f.url)) {
                    seen.add(f.url);
                    links.push({ titulo: f.nome, url: f.url, orgao: f.orgao });
                }
            });
        direitosData.forEach((cat) => {
            (cat.links || []).forEach((lk) => {
                if (!seen.has(lk.url)) {
                    seen.add(lk.url);
                    links.push({ titulo: lk.titulo, url: lk.url, orgao: '' });
                }
            });
        });
        // Helper: match exato de host ou subdomínio
        const hostMatches = (host, suffix) =>
            host === suffix || host.endsWith('.' + suffix);
        
        // v1.43.37: classificação combina host + primeiro segmento de path.
        // Portais consolidados em www.gov.br/<orgao>/... antes caíam no balde
        // "Gov.BR" — agora vão para INSS/Saúde/MDS/MEC quando aplicável.
        const categorias = {
            'Planalto':  { hosts: ['planalto.gov.br'], paths: [] },
            'INSS':      { hosts: ['inss.gov.br'],     paths: ['/inss'] },
            'MDS':       { hosts: ['mds.gov.br'],      paths: ['/mds'] },
            'MEC':       { hosts: ['mec.gov.br'],      paths: ['/mec', '/inep', '/fnde'] },
            'Saúde':     { hosts: ['saude.gov.br', 'ans.gov.br', 'anvisa.gov.br'], paths: ['/saude', '/ans', '/anvisa'] },
            'OMS':       { hosts: ['who.int'],         paths: [] },
            'Conselhos': { hosts: ['cfm.org.br', 'cfp.org.br'], paths: [] },
            'Gov.BR':    { hosts: [], paths: [] },  // balde genérico
        };

        function classifyLink(host, pathname) {
            for (const [cat, { hosts }] of Object.entries(categorias)) {
                if (hosts.some((h) => hostMatches(host, h))) return cat;
            }
            if (host === 'gov.br' || host.endsWith('.gov.br')) {
                const firstSeg = '/' + ((pathname || '').split('/').filter(Boolean)[0] || '');
                for (const [cat, { paths }] of Object.entries(categorias)) {
                    if (paths.some((p) => firstSeg === p)) return cat;
                }
                return 'Gov.BR';
            }
            return 'Outros';
        }

        function parseHostPath(url) {
            try {
                const u = new URL(url, window.location.origin);
                if (u.protocol === 'tel:') return { host: 'tel', pathname: '' };
                return { host: u.hostname.replace(/^www\./, ''), pathname: u.pathname || '' };
            } catch {
                return { host: '', pathname: '' };
            }
        }

        function renderGrid(filter) {
            const filtered = filter === 'todos'
                ? links
                : links.filter((lk) => {
                    const { host, pathname } = parseHostPath(lk.url);
                    return classifyLink(host, pathname) === filter;
                });
            
            if (filtered.length === 0) {
                dom.linksGrid.innerHTML = '<p style="text-align:center;color:var(--text-muted);">Nenhum link nesta categoria.</p>';
                return;
            }
            
            dom.linksGrid.innerHTML = filtered
                .filter((lk) => isSafeUrl(lk.url))
                .map((lk) => {
                    let parsedUrl = null;
                    try { parsedUrl = new URL(lk.url, window.location.origin); }
                    catch { /* te l:/blob:/mailto: já filtrados */ }
                    const isTel = parsedUrl?.protocol === 'tel:';
                    const domain = (() => {
                        if (isTel) return (parsedUrl.pathname || lk.url.replace(/^tel:/i, ''));
                        try { return new URL(lk.url).hostname.replace(/^www\./, ''); }
                        catch { return ''; }
                    })();
                    return `
<a href="${escapeHtml(lk.url)}" class="link-card" target="_blank" rel="noopener noreferrer">
<span class="link-title">${escapeHtml(lk.titulo)}</span>
<span class="link-domain">${escapeHtml(domain)}</span>
</a>`;
                })
                .join('');
        }
        
        renderGrid('todos');
        document.querySelectorAll('.links-filter-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.links-filter-btn').forEach((b) => {
                    b.classList.remove('active');
                    b.setAttribute('aria-pressed', 'false');
                });
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
                renderGrid(btn.dataset.filter);
            });
        });
    }
    function renderHeroStats() {
        if (!direitosData || !fontesData) return;
        if (dom.heroCatCount) {
            dom.heroCatCount.textContent = `${direitosData.length}`;
        }
        if (dom.heroFontesCount) {
            dom.heroFontesCount.textContent = `${fontesData.length}`;
        }
    }
    function renderOrgaosEstaduais() {
        if (!orgaosEstaduaisData || !dom.orgaosEstaduaisGrid) return;
        const regioes = {
            'Norte': ['AC', 'AM', 'AP', 'PA', 'RO', 'RR', 'TO'],
            'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
            'Centro-Oeste': ['DF', 'GO', 'MS', 'MT'],
            'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
            'Sul': ['PR', 'RS', 'SC'],
        };
        // v1.43.22 — UF → slug de região para data-regiao no card (cor da badge).
        const ufToRegiaoSlug = {};
        for (const [nome, ufs] of Object.entries(regioes)) {
            const slug = nome.toLowerCase().replace(/\s+/g, '-');
            ufs.forEach((uf) => { ufToRegiaoSlug[uf] = slug; });
        }
        let activeFilter = 'todos';
        function renderGrid(filter) {
            const filtered = filter === 'todos'
                ? orgaosEstaduaisData
                : orgaosEstaduaisData.filter((o) => {
                    const states = regioes[filter] || [];
                    return states.includes(o.uf);
                });
            if (filtered.length === 0) {
                dom.orgaosEstaduaisGrid.innerHTML = '<p style="text-align:center;color:var(--text-muted);">Nenhum órgão nesta região.</p>';
                return;
            }
            dom.orgaosEstaduaisGrid.innerHTML = filtered
                .map((org) => {
                    const urlSafe = isSafeUrl(org.url);
                    const regiaoSlug = ufToRegiaoSlug[org.uf] || '';
                    return `
<div class="orgao-card"${regiaoSlug ? ` data-regiao="${escapeHtml(regiaoSlug)}"` : ''}>
<span class="orgao-uf-badge">${escapeHtml(org.uf)}</span>
<span class="orgao-nome">${escapeHtml(org.nome)}</span>
${urlSafe ? `<a href="${escapeHtml(org.url)}" class="btn btn-sm btn-outline orgao-link" target="_blank" rel="noopener noreferrer">
Acessar ↗
</a>` : ''}
</div>`;
                })
                .join('');
        }
        renderGrid('todos');
        document.querySelectorAll('.orgao-filter-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.orgao-filter-btn').forEach((b) => {
                    b.classList.remove('active');
                    b.setAttribute('aria-pressed', 'false');
                });
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
                activeFilter = btn.dataset.filter;
                renderGrid(activeFilter);
            });
        });
    }
    function renderClassificacao() {
        if (!classificacaoData || !dom.classificacaoGrid) return;
        dom.classificacaoGrid.innerHTML = `
<div class="classif-table-wrapper">
<table class="classif-table">
<thead>
<tr>
<th>Tipo de Deficiência</th>
<th>CID-10</th>
<th>CID-11</th>
<th>Critério Técnico</th>
</tr>
</thead>
<tbody>
${classificacaoData.map((c) => `
<tr>
<td class="classif-tipo" data-label="Tipo"><strong>${escapeHtml(c.tipo)}</strong></td>
<td class="classif-cid" data-label="CID-10"><code>${escapeHtml(Array.isArray(c.cid10) ? c.cid10.join(', ') : (c.cid10 || ''))}</code></td>
<td class="classif-cid" data-label="CID-11"><code>${escapeHtml(Array.isArray(c.cid11) ? c.cid11.join(', ') : (c.cid11 || ''))}</code></td>
<td class="classif-criterio" data-label="Critério">${escapeHtml(c.criterio)}</td>
</tr>`).join('')}
</tbody>
</table>
</div>
<p class="classif-note">
<strong>Observação:</strong> a CID-11 (OMS 2022) está sendo adotada gradualmente.
No Brasil, a maioria dos laudos ainda usa CID-10. O sistema aceita ambas as codificações.
</p>`;
    }
    function checkStaleness() {
        if (!jsonMeta || !dom.stalenessBanner) return;
        const updated = new Date(jsonMeta.ultima_atualizacao);
        const now = new Date();
        const diffDays = Math.floor((now - updated) / (1000 * 60 * 60 * 24));
        const STALE_THRESHOLD = 30;
        if (diffDays > STALE_THRESHOLD) {
            if (dom.staleDays) {
                dom.staleDays.textContent = `há ${diffDays} dias`;
            }
            dom.stalenessBanner.hidden = false;
        } else {
            dom.stalenessBanner.hidden = true;
        }
    }
    function revealDocsUpload() {
        const area = document.getElementById('docsUploadArea');
        if (!area) return;
        // hidden attribute (preferred) ou fallback display:none legado
        if (area.hasAttribute('hidden')) area.removeAttribute('hidden');
        if (area.style.display === 'none') area.style.display = '';
    }
    (function setupDocsReveal() {
        const heroBtn = document.getElementById('heroDocsBtn');
        if (heroBtn) {
            heroBtn.addEventListener('click', revealDocsUpload);
        }
    })();
    function setupUpload() {
        if (!dom.uploadZone || !dom.fileInput || !dom.deleteAllFiles) return;
        dom.uploadZone.addEventListener('click', () => dom.fileInput.click());
        dom.uploadZone.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                dom.fileInput.click();
            }
        });
        dom.fileInput.addEventListener('change', async (e) => {
            await handleFiles(e.target.files);
            e.target.value = '';
            revealDocsUpload();
        });
        dom.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dom.uploadZone.classList.add('drag-over');
        });
        dom.uploadZone.addEventListener('dragleave', () => {
            dom.uploadZone.classList.remove('drag-over');
        });
        dom.uploadZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            dom.uploadZone.classList.remove('drag-over');
            await handleFiles(e.dataTransfer.files);
            revealDocsUpload();
        });
        dom.deleteAllFiles.addEventListener('click', () => {
            confirmAction('Tem certeza? Todos os arquivos serão removidos permanentemente do seu navegador.', async () => {
                await clearAllFiles();
                await renderFileList();
            });
        });
    }
    async function handleFiles(fileList) {
        const currentCount = await getFileCount();
        const filesToAdd = Array.from(fileList);
        if (currentCount + filesToAdd.length > MAX_FILES) {
            showToast(`Limite de ${MAX_FILES} arquivos. Pode adicionar mais ${MAX_FILES - currentCount}.`, 'warning');
            return;
        }
        for (const file of filesToAdd) {
            if (!ALLOWED_TYPES.includes(file.type)) {
                const parts = file.name.split('.');
                const ext = parts.length > 1 ? parts.pop().toLowerCase() : '';
                if (!ALLOWED_EXTENSIONS.includes('.' + ext)) {
                    showToast(`Formato não aceito: ${file.name}. Use PDF, JPG ou PNG.`, 'error');
                    continue;
                }
            }
            if (file.size > MAX_FILE_SIZE) {
                showToast(`Arquivo muito grande: ${file.name} (${formatBytes(file.size)}). Máx: 5MB.`, 'error');
                continue;
            }
            try {
                const buffer = await file.arrayBuffer();
                const encrypted = await encryptBuffer(buffer);
                const now = new Date();
                const expires = new Date(now.getTime() + FILE_TTL_MINUTES * 60000);
                await storeFile({
                    id: Date.now() + '_' + Math.random().toString(36).slice(2, 8),
                    name: file.name,
                    type: file.type,
                    size: file.size,
                    data: encrypted.ciphertext,
                    iv: encrypted.iv,
                    encrypted: true,
                    addedAt: now.toISOString(),
                    expiresAt: expires.toISOString(),
                });
            } catch (err) {
                console.error('Erro ao salvar arquivo:', err);
                showToast(`Erro ao salvar: ${file.name}`, 'error');
            }
        }
        await renderFileList();
    }
    async function renderFileList() {
        try {
            const files = await getAllFiles();
            const area = document.getElementById('docsUploadArea');
            if (files.length === 0) {
                dom.fileList.innerHTML = '';
                dom.deleteAllFiles.style.display = 'none';
                // Esconde área de upload quando não há arquivos (mantém UI limpa)
                if (area && !area.hasAttribute('hidden')) area.setAttribute('hidden', '');
                return;
            }
            // Garante área visível quando há arquivos
            if (area && area.hasAttribute('hidden')) area.removeAttribute('hidden');
            dom.deleteAllFiles.style.display = '';
            dom.fileList.innerHTML = files
                .map((f) => {
                    const tipoLabel = f.type === 'application/pdf' ? 'PDF' : 'Imagem';
                    const date = new Date(f.addedAt).toLocaleDateString('pt-BR');
                    const cryptoBadge = f.encrypted ? '<span class="crypto-badge" title="Criptografia AES-256-GCM">criptografado</span>' : '';
                    const expiresStr = f.expiresAt
                        ? `· expira em ${formatTimeRemaining(f.expiresAt)}`
                        : '';
                    return `
<div class="file-item" data-file-id="${f.id}">
<label class="file-item-checkbox" title="Selecionar para análise">
<input type="checkbox" class="file-select-cb" data-id="${f.id}" checked>
</label>
<span class="file-item-icon" aria-hidden="true">${tipoLabel}</span>
<div class="file-item-info">
<div class="file-item-name" title="${escapeHtml(f.name)}">${cryptoBadge}${escapeHtml(f.name)}</div>
<div class="file-item-meta">${formatBytes(f.size)} · Adicionado em ${date} ${expiresStr}</div>
</div>
<div class="file-item-actions">
<button class="btn-view" title="Visualizar" data-id="${f.id}">Ver</button>
<button class="btn-delete" title="Excluir" data-id="${f.id}" aria-label="Excluir arquivo">Excluir</button>
</div>
</div>`;
                })
                .join('');
            updateAnalyzeButton();
            dom.fileList.querySelectorAll('.file-select-cb').forEach((cb) => {
                cb.addEventListener('change', updateAnalyzeButton);
            });
            dom.fileList.querySelectorAll('.btn-view').forEach((btn) => {
                btn.addEventListener('click', async () => {
                    const file = await getFile(btn.dataset.id);
                    if (file) {
                        const plainData = await decryptFileData(file);
                        if (!plainData) return;
                        const blob = new Blob([plainData], { type: file.type });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.target = '_blank';
                        a.rel = 'noopener';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        setTimeout(() => URL.revokeObjectURL(url), 15000);
                    }
                });
            });
            dom.fileList.querySelectorAll('.btn-delete').forEach((btn) => {
                btn.addEventListener('click', () => {
                    confirmAction('Excluir este arquivo?', async () => {
                        await deleteFile(btn.dataset.id);
                        await renderFileList();
                    });
                });
            });
        } catch (err) {
            console.error('Erro ao listar arquivos:', err);
        }
    }
    function updateAnalyzeButton() {
        const btn = document.getElementById('analyzeSelected');
        const btnAI = document.getElementById('analyzeWithAI');
        const checked = dom.fileList.querySelectorAll('.file-select-cb:checked');
        const count = checked.length;
        if (btn) {
            btn.disabled = count === 0;
            btn.textContent = count === 0
                ? 'Enviar para análise local'
                : count === 1
                    ? 'Analisar 1 arquivo'
                    : `Analisar ${count} arquivos`;
        }
        if (btnAI) {
            btnAI.disabled = count === 0;
            btnAI.textContent = count === 0
                ? 'Analisar com IA (servidor)'
                : count === 1
                    ? 'Analisar 1 arquivo com IA'
                    : `Analisar ${count} arquivos com IA`;
        }
    }
    function setupAnalysis() {
        if (dom.closeAnalysis) {
            dom.closeAnalysis.addEventListener('click', () => {
                dom.analysisResults.style.display = 'none';
            });
        }

        if (dom.exportPdf) {
            dom.exportPdf.addEventListener('click', () => {
                dom.analysisResults.setAttribute('data-print-date', new Date().toLocaleDateString('pt-BR'));
                document.body.classList.add('printing-analysis');
                window.print();
                const cleanup = () => {
                    document.body.classList.remove('printing-analysis');
                    window.removeEventListener('afterprint', cleanup);
                };
                window.addEventListener('afterprint', cleanup);
                setTimeout(cleanup, 5000);
            });
        }

        const shareAnalysisBtn = document.getElementById('shareAnalysisWhatsApp');
        if (shareAnalysisBtn) {
            shareAnalysisBtn.addEventListener('click', () => {
                const analysisTitle = document.querySelector('.analysis-results h3')?.textContent || 'Análise';
                const matches = document.querySelectorAll('.analysis-match');
                const matchList = Array.from(matches).map((m, i) => `${i + 1}. ${m.querySelector('.analysis-match-title h4')?.textContent || 'Direito'}`).join('\n');
                // Princípio 1 (Transparência) — incluir disclosure quando IA foi usada na análise compartilhada.
                const aiBanner = document.getElementById('aiDisclosureBanner');
                const aiUsed = aiBanner && !aiBanner.hidden;
                const aiFooter = aiUsed
                    ? '\n\nConteúdo gerado por IA (Azure OpenAI gpt-4o-mini, Brasil Sul) — confirme no .gov.br.'
                    : '';
                const text = `*${analysisTitle}*\n\n${matchList}\n\nVeja mais em: ${window.location.origin}${aiFooter}`;
                const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
                const win = window.open(url, '_blank', 'noopener,noreferrer');
                if (!win) {
                    const a = document.createElement('a');
                    a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer';
                    document.body.appendChild(a); a.click(); a.remove();
                }
            });
        }
        const exportDocsChecklistBtn = document.getElementById('exportDocsChecklistPdf');
        if (exportDocsChecklistBtn) {
            exportDocsChecklistBtn.addEventListener('click', () => {
                const container = document.querySelector('#consultar > .container');
                if (container) {
                    container.setAttribute('data-print-date', new Date().toLocaleDateString('pt-BR'));
                }
                document.body.classList.add('printing-docs-checklist');
                window.print();
                const cleanup = () => {
                    document.body.classList.remove('printing-docs-checklist');
                    window.removeEventListener('afterprint', cleanup);
                };
                window.addEventListener('afterprint', cleanup);
                setTimeout(cleanup, 5000);
            });
        }
        const shareDocsBtn = document.getElementById('shareDocsWhatsApp');
        if (shareDocsBtn) {
            shareDocsBtn.addEventListener('click', () => {
                const shareText = encodeURIComponent(
                    `Documentos necessários por direito — lista completa\n\n` +
                    `Lista organizada de 16 documentos essenciais para garantir direitos PcD:\n` +
                    `• Laudos médicos\n` +
                    `• Documentos pessoais\n` +
                    `• Comprovantes de renda\n` +
                    `• E mais...\n\n` +
                    `Confira a lista completa: https://nossodireito.fabiotreze.com\n\n` +
                    `100% gratuito — zero coleta de dados — baseado na legislação brasileira`
                );
                const url = `https://wa.me/?text=${shareText}`;
                const win = window.open(url, '_blank', 'noopener,noreferrer');
                if (!win) {
                    const a = document.createElement('a');
                    a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer';
                    document.body.appendChild(a); a.click(); a.remove();
                }
            });
        }
        const analyzeBtn = document.getElementById('analyzeSelected');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => analyzeSelectedDocuments(false));
        }
        const analyzeAIBtn = document.getElementById('analyzeWithAI');
        if (analyzeAIBtn) {
            analyzeAIBtn.addEventListener('click', () => analyzeSelectedDocuments(true));
        }
    }
    async function analyzeSelectedDocuments(useAI = false) {
        const analyzeBtn = document.getElementById('analyzeSelected');
        const analyzeAIBtn = document.getElementById('analyzeWithAI');
        const checkboxes = dom.fileList.querySelectorAll('.file-select-cb:checked');
        const fileIds = Array.from(checkboxes).map((cb) => cb.dataset.id);
        if (fileIds.length === 0) {
            showToast('Selecione pelo menos um arquivo para analisar.', 'warning');
            return;
        }
        if (analyzeBtn) {
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = 'Analisando...';
        }
        if (analyzeAIBtn) {
            analyzeAIBtn.disabled = true;
            if (useAI) analyzeAIBtn.textContent = 'Anonimizando e enviando para IA...';
        }
        dom.analysisResults.style.display = '';
        dom.analysisLoading.style.display = '';
        dom.analysisContent.innerHTML = '';
        dom.analysisResults.scrollIntoView({ behavior: 'smooth' });
        const allText = [];
        const fileNames = [];
        const hasPdf = [];
        const errors = [];
        const successIds = [];
        try {
            const filesToProcess = [];
            for (const fileId of fileIds) {
                try {
                    const file = await getFile(fileId);
                    if (!file) {
                        errors.push({ name: `ID ${fileId}`, reason: 'Arquivo não encontrado' });
                    } else {
                        filesToProcess.push({ fileId, file });
                    }
                } catch (dbErr) {
                    console.error(`Erro ao recuperar arquivo ${fileId}:`, dbErr);
                    errors.push({ name: `ID ${fileId}`, reason: 'Erro ao acessar arquivo' });
                }
            }
            for (let i = 0; i < filesToProcess.length; i++) {
                const { fileId, file } = filesToProcess[i];
                if (filesToProcess.length > 1) {
                    const loadingText = dom.analysisLoading.querySelector('p');
                    if (loadingText) {
                        loadingText.textContent = `Analisando ${i + 1} de ${filesToProcess.length}: ${file.name}`;
                    }
                }
                try {
                    const plainData = await decryptFileData(file);
                    if (!plainData) throw new Error('Decryption failed');
                    let text = '';
                    if (file.type === 'application/pdf') {
                        text = await extractPdfText(plainData);
                        hasPdf.push(true);
                    } else {
                        text = file.name;
                        hasPdf.push(false);
                    }
                    allText.push(text);
                    fileNames.push(file.name);
                    successIds.push(fileId);
                } catch (err) {
                    console.error(`Erro ao processar ${file.name}:`, err);
                    errors.push({
                        name: file.name,
                        reason: file.type === 'application/pdf'
                            ? 'PDF protegido, escaneado ou formato incompatível'
                            : 'Erro ao processar imagem',
                    });
                }
            }
            if (allText.length === 0) {
                dom.analysisContent.innerHTML = `
<div class="analysis-error">
<p><strong>⚠️ Não foi possível analisar nenhum dos arquivos selecionados.</strong></p>
${errors.map((e) => `<p style=\"font-size:0.85rem;color:var(--text-muted);\">· ${escapeHtml(e.name)}: ${escapeHtml(e.reason)}</p>`).join('')}
<p style="font-size:0.85rem;margin-top:8px;">
Navegue pelas <a href=\"#categorias\">categorias</a>
para encontrar seus direitos manualmente.
</p>
</div>`;
                return;
            }
            const originalText = allText.join('\n');
            // v1.43.38: gate multidimensional substitui o "1 palavra basta".
            // Exige CRM/CRP/COFFITO/... OU CID válido + score >=5 de corroboração.
            // Sem isso, texto não-clínico (boleto, bula, boletim escolar) entrava
            // no matchRights e gerava sugestões de direitos sem fundamento.
            const validation = (window.DocumentValidator && window.DocumentValidator.validate)
                ? window.DocumentValidator.validate(originalText)
                : { accepted: true, score: 0, signals: {}, reasons: [] };
            if (!validation.accepted) {
                const reasonsHtml = (validation.reasons || [])
                    .map((r) => `<li>${escapeHtml(r)}</li>`)
                    .join('');
                dom.analysisContent.innerHTML = `
<div class="analysis-error">
<p><strong>⚠️ O arquivo não parece ser um laudo, atestado ou relatório médico.</strong></p>
<p>Para evitar sugerir direitos que não têm a ver com o seu documento, precisamos identificar pelo menos um destes itens:</p>
<ul style="margin:6px 0 6px 22px;font-size:0.95rem;">
  <li>Registro de profissional de saúde (CRM, CRP, COFFITO, CRF, CREFITO, CRO, CRN ou CREFONO); <strong>OU</strong></li>
  <li>Código de diagnóstico (CID-10, ex.: F84.0, Q90; ou CID-11, ex.: 6A02.0).</li>
</ul>
<p style="font-size:0.9rem;">Também ajuda quando o documento usa termos clínicos como <em>diagnóstico</em>, <em>anamnese</em>, <em>evolução clínica</em> ou <em>prognóstico</em>.</p>
${reasonsHtml ? `<details style="margin-top:8px;font-size:0.85rem;color:var(--text-muted);"><summary>Por que este arquivo foi recusado</summary><ul style="margin:4px 0 4px 22px;">${reasonsHtml}</ul></details>` : ''}
<p style="font-size:0.9rem;margin-top:8px;">
Navegue pelas <a href="#categorias">categorias</a> para encontrar seus direitos sem precisar enviar documento.
</p>
</div>`;
                for (const id of successIds) {
                    try { await deleteFile(id); } catch (delErr) { console.warn('Erro ao descartar arquivo após análise:', delErr); }
                }
                await renderFileList();
                if (analyzeBtn) updateAnalyzeButton();
                dom.analysisLoading.style.display = 'none';
                return;
            }
            const combinedNames = fileNames.join(' ');
            const results = matchRights(originalText, combinedNames);
            const anyPdf = hasPdf.some(Boolean);
            let aiResult = null;
            let aiAttempted = false;
            if (useAI) {
                try {
                    aiAttempted = true;
                    const consent = await getAIConsent();
                    if (!consent) {
                        errors.push({ name: 'Análise IA', reason: 'Consentimento LGPD não concedido.' });
                    } else if (!window.Anonymizer || typeof window.Anonymizer.anonymize !== 'function') {
                        errors.push({ name: 'Análise IA', reason: 'Anonymizer não carregado no navegador.' });
                    } else {
                        const { text: anonymized, stats: anonStats } = window.Anonymizer.anonymize(originalText);
                        console.info('[AI] Anonimização local concluída:', anonStats);
                        aiResult = await callServerAnalysis(anonymized);
                    }
                } catch (aiErr) {
                    console.error('Erro análise IA:', aiErr);
                    errors.push({ name: 'Análise IA', reason: aiErr.message || 'Falha no servidor.' });
                    if (typeof showToast === 'function') {
                        showToast('IA indisponível no momento. Resultado exibido com análise local.', 'warning');
                    }
                }
            }
            renderAnalysisResults(results, fileNames, anyPdf, errors, aiResult, aiAttempted);
            for (const id of successIds) {
                try {
                    await deleteFile(id);
                } catch (delErr) {
                    console.warn('Erro ao descartar arquivo após análise:', delErr);
                }
            }
            console.info(`[Security] ${successIds.length} arquivo(s) descartado(s) automaticamente após análise.`);
            await renderFileList();
        } catch (err) {
            console.error('Erro na análise unificada:', err);
            dom.analysisContent.innerHTML = `
<div class="analysis-error">
<p><strong>⚠️ Ocorreu um erro durante a análise.</strong></p>
<p style="font-size:0.85rem;margin-top:8px;">
Navegue pelas <a href=\"#categorias\">categorias</a>
para encontrar seus direitos manualmente.
</p>
</div>`;
        } finally {
            dom.analysisLoading.style.display = 'none';
            const loadingText = dom.analysisLoading.querySelector('p');
            if (loadingText) {
                loadingText.textContent = 'Analisando documentos... (100% local, nada é enviado)';
            }
            if (analyzeBtn) {
                updateAnalyzeButton();
            }
        }
    }
    async function extractPdfText(arrayBuffer) {
        await ensurePdfJs();
        if (typeof pdfjsLib === 'undefined') {
            throw new Error('pdf.js não disponível');
        }
        const pdf = await pdfjsLib.getDocument({ data: new Uint8Array(arrayBuffer) }).promise;
        const textParts = [];
        for (let i = 1; i <= Math.min(pdf.numPages, 20); i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            const pageText = content.items.map((item) => item.str).join(' ');
            textParts.push(pageText);
        }
        return textParts.join('\n');
    }
    function cidGenericRegex() { return /\b([A-Z]\d{2}(?:\.\d{1,2})?)\b/g; }
    function cid11GenericRegex() { return /\b(\d[A-Z]\d{2}(?:\.\d{1,2})?)\b/g; }
    function cid11TwoLetterRegex() { return /\b([A-Z]{2}\d{2}(?:\.\d{1,2})?)\b/g; }
    function crmRegex() { return /\bCRM[\s/\-]*([A-Z]{2})?[\s/\-]*(\d{4,7})[\s/\-]*([A-Z]{2})?\b/gi; }
    function matchRights(text, fileName) {
        if (!direitosData) return [];
        const rawText = text + ' ' + fileName;
        const normalizedText = normalizeText(rawText);
        const scores = {};
        direitosData.forEach((cat) => {
            scores[cat.id] = { score: 0, matches: new Set() };
        });
        const cidMatched = new Set();
        for (const cidRegex of [cidGenericRegex(), cid11GenericRegex(), cid11TwoLetterRegex()]) {
            let m;
            while ((m = cidRegex.exec(rawText)) !== null) {
                const code = m[1];
                const prefix = code.substring(0, 3).toLowerCase();
                if (KEYWORD_MAP[prefix] || KEYWORD_MAP[code.toLowerCase()]) continue;
                if (cidMatched.has(code)) continue;
                cidMatched.add(code);
                const letter = code.charAt(0);
                const cats = CID_RANGE_MAP[letter] || ['bpc', 'sus_terapias'];
                cats.forEach((catId) => {
                    if (scores[catId]) {
                        scores[catId].score += 3;
                        scores[catId].matches.add(`CID ${code}`);
                    }
                });
            }
        }
        const crmMatch = crmRegex().exec(rawText);
        if (crmMatch) {
            const uf = crmMatch[1] || crmMatch[3] || '';
            const num = crmMatch[2];
            const crmLabel = uf ? `CRM/${uf} ${num}` : `CRM ${num}`;
            ['bpc', 'ciptea', 'plano_saude', 'sus_terapias', 'transporte', 'trabalho', 'fgts'].forEach((catId) => {
                if (scores[catId]) {
                    scores[catId].score += 2;
                    scores[catId].matches.add(crmLabel);
                }
            });
        }
        const seenNormalized = new Set();
        for (const [keyword, { cats, weight }] of Object.entries(KEYWORD_MAP)) {
            const normalizedKey = normalizeText(keyword);
            if (seenNormalized.has(normalizedKey)) continue;
            seenNormalized.add(normalizedKey);
            let matchCount;
            if (UPPERCASE_ONLY_TERMS.has(normalizedKey)) {
                const upperKey = keyword.toUpperCase();
                const safeB = '(?:^|[\\s,.;:()\\[\\]/\\-])';
                const safeA = '(?=$|[\\s,.;:()\\[\\]/\\-])';
                const regex = new RegExp(safeB + escapeRegex(upperKey) + safeA, 'g');
                matchCount = (rawText.match(regex) || []).length;
            } else {
                const regex = new RegExp('\\b' + escapeRegex(normalizedKey) + '\\b', 'g');
                matchCount = (normalizedText.match(regex) || []).length;
            }
            if (matchCount > 0) {
                cats.forEach((catId) => {
                    if (scores[catId]) {
                        scores[catId].score += weight * Math.min(matchCount, 3);
                        scores[catId].matches.add(keyword);
                    }
                });
            }
        }
        direitosData.forEach((cat) => {
            (cat.tags || []).forEach((tag) => {
                const normalizedTag = normalizeText(tag);
                if (UPPERCASE_ONLY_TERMS.has(normalizedTag)) {
                    const upperTag = tag.toUpperCase();
                    const safeB = '(?:^|[\\s,.;:()\\[\\]/\\-])';
                    const safeA = '(?=$|[\\s,.;:()\\[\\]/\\-])';
                    const regex = new RegExp(safeB + escapeRegex(upperTag) + safeA);
                    if (regex.test(rawText)) {
                        scores[cat.id].score += 2;
                        scores[cat.id].matches.add(tag);
                    }
                    return;
                }
                if (normalizedTag.length <= 5) {
                    const tagRegex = new RegExp('\\b' + escapeRegex(normalizedTag) + '\\b');
                    if (tagRegex.test(normalizedText)) {
                        scores[cat.id].score += 2;
                        scores[cat.id].matches.add(tag);
                    }
                } else if (normalizedText.includes(normalizedTag)) {
                    scores[cat.id].score += 2;
                    scores[cat.id].matches.add(tag);
                }
            });
        });
        direitosData.forEach((cat) => {
            (cat.requisitos || []).forEach((req) => {
                const words = normalizeText(req).split(/\s+/).filter((w) => w.length > 4);
                const matchedWords = words.filter((w) => {
                    const wRegex = new RegExp('\\b' + escapeRegex(w) + '\\b');
                    return wRegex.test(normalizedText);
                });
                if (matchedWords.length >= 2) {
                    scores[cat.id].score += 1;
                }
            });
        });
        return direitosData
            .map((cat) => ({
                category: cat,
                score: scores[cat.id].score,
                matches: Array.from(scores[cat.id].matches),
            }))
            .filter((r) => r.score > 0)
            .sort((a, b) => b.score - a.score);
    }
    function renderAnalysisResults(results, fileNames, hasPdf, errors = [], aiResult = null, aiAttempted = false) {
        // Cache análise para recuperação ao voltar
        if (typeof window.ANALYSIS_CACHE !== 'undefined') {
            window.ANALYSIS_CACHE.save({
                results,
                fileNames,
                hasPdf,
                errors,
                aiResult,
                aiAttempted
            }).catch(err => console.warn('Falha ao cachear análise:', err));
        }
        // Princípio 1 (Transparência) — https://learn.microsoft.com/en-gb/principles-for-ai-generated-content
        // Banner persistente quando IA foi efetivamente usada (aiResult presente).
        const aiBanner = document.getElementById('aiDisclosureBanner');
        if (aiBanner) {
            aiBanner.hidden = !aiResult;
        }
        const names = Array.isArray(fileNames) ? fileNames : [fileNames];
        const fileCount = names.length;
        const filesLabel = fileCount === 1
            ? `Arquivo analisado: <strong>${escapeHtml(names[0])}</strong>`
            : `${fileCount} arquivos analisados: ${names.map((n) => `<strong>${escapeHtml(n)}</strong>`).join(', ')}`;
        if (results.length === 0) {
            dom.analysisContent.innerHTML = `
<div class="analysis-empty">
<p>${filesLabel}</p>
<p>Não foram encontradas correspondências claras com as categorias de direitos.</p>
${!hasPdf ? `<p class="analysis-hint">Para imagens, a análise é limitada ao nome do arquivo.
Faça upload do <strong>PDF do laudo</strong> para uma análise mais completa.</p>` : ''}
${errors.length ? `<div class="analysis-errors-summary">
<p><strong>⚠️ Alguns arquivos não puderam ser processados:</strong></p>
${errors.map((e) => `<p class="analysis-hint">· ${escapeHtml(e.name)}: ${escapeHtml(e.reason)}</p>`).join('')}
</div>` : ''}
<p class="analysis-hint">Navegue pelas <a href="#categorias">categorias</a> para encontrar
seus direitos manualmente, ou use a <a href="#consultar">busca</a>.</p>
</div>`;
            return;
        }
        const maxScore = results[0].score;
        const privacyLine = aiResult
            ? 'Análise local + IA opcional (texto anonimizado antes do envio).'
            : aiAttempted
            ? 'Análise local concluída. IA indisponível ou sem consentimento — nenhum dado adicional foi enviado.'
            : 'Análise 100% local — nenhum dado foi enviado para servidores.';
        // Adicionar state à navegação para recuperação de análise
        if (history.pushState) history.pushState({ view: 'analysis' }, '', '#analise');
        let html = `
<div class="analysis-file-info">
<p>${filesLabel}</p>
    <p class="analysis-privacy">${privacyLine}</p>
${errors.length ? `<p class="analysis-errors-inline"><strong>⚠️ ${errors.length} arquivo(s) com erro:</strong> ${errors.map((e) => escapeHtml(e.name)).join(', ')}</p>` : ''}
</div>
<div class="analysis-legend" aria-label="Legenda da precisão">
<span class="legend-badge high">Alta relevância</span>
<span class="legend-badge medium">Média relevância</span>
<span class="legend-badge low">Possível relação</span>
<span class="legend-bar"><span class="legend-bar-sample high" aria-hidden="true"></span><span class="legend-bar-sample medium" aria-hidden="true"></span><span class="legend-bar-sample low" aria-hidden="true"></span> Barra indica grau de correspondência</span>
</div>
<div class="analysis-match-list">`;
        results.forEach(({ category, score, matches }) => {
            const pct = Math.round((score / maxScore) * 100);
            const level = pct >= 80 ? 'high' : pct >= 40 ? 'medium' : 'low';
            const levelLabel = pct >= 80 ? 'Alta relevância' : pct >= 40 ? 'Média relevância' : 'Possível relação';
            const barPct = level === 'high' ? Math.max(85, pct) : level === 'medium' ? Math.round(45 + (pct - 40) * 0.625) : Math.round(15 + pct * 0.5);
            html += `
<div class="analysis-match ${level}" data-cat-id="${category.id}" aria-label="${levelLabel}">
<div class="analysis-match-header">
<div class="analysis-match-title">
<h4>${escapeHtml(category.titulo)}</h4>
<span class="analysis-badge ${level}" aria-label="${levelLabel}">${levelLabel}</span>
</div>
<div class="analysis-bar-group">
<span class="analysis-bar-label ${level}">${level === 'high' ? 'Alta' : level === 'medium' ? 'Média' : 'Baixa'}</span>
<div class="analysis-match-bar" role="img" aria-label="${levelLabel}: ${barPct}%">
<div class="analysis-match-fill ${level}" style="width:${barPct}%"></div>
</div>
</div>
</div>
<p class="analysis-match-resumo">${escapeHtml(category.resumo)}</p>
${matches.length ? `
<div class="analysis-match-keywords">
<span class="kw-label"><strong>Termos encontrados:</strong></span>
${matches.slice(0, 8).map((m) => {
                if (m.startsWith('CID')) {
                    const cidNum = m.match(/CID\s+([A-Z0-9.]+)/);
                    return cidNum ? `<span class="kw-tag ${level}">${escapeHtml(m)}</span>` : `<span class="kw-tag low">CID não identificado</span>`;
                }
                if (m.startsWith('CRM')) {
                    const crmNum = m.match(/CRM\/?[A-Z]{0,2}\s*\d{4,7}/);
                    return crmNum ? `<span class="kw-tag ${level}">${escapeHtml(m)}</span>` : `<span class="kw-tag low">CRM não identificado</span>`;
                }
                return `<span class="kw-tag ${level}">${escapeHtml(m)}</span>`;
            }).join('')}
</div>` : ''}
<div class="analysis-match-actions">
<button class="btn btn-sm btn-primary analysis-see-more" data-id="${category.id}">
Ver detalhes e passo a passo →
</button>
</div>
</div>`;
        });
        html += `</div>
    ${aiResult ? renderAIPracticalSummary(aiResult, results) : ''}
    ${aiResult ? renderAIResult(aiResult) : ''}
    ${aiResult ? renderHumanReviewButton() : ''}
<div class="analysis-footer">
<p><strong>⚠️ Atenção:</strong> esta análise é uma <strong>correspondência de palavras-chave</strong>
com o catálogo; <strong>não é parecer profissional</strong>. A confirmação cabe à
<strong>Defensoria Pública</strong> (CF Art. 134), a um(a) advogado(a) (Lei 8.906/1994) ou ao <strong>CRAS</strong> (Lei 8.742/1993) da sua cidade.</p>
</div>`;
        dom.analysisContent.innerHTML = html;
        dom.analysisContent.querySelectorAll('.analysis-see-more').forEach((btn) => {
            btn.addEventListener('click', () => {
                showDetalhe(btn.dataset.id);
                dom.analysisResults.style.display = 'none';
            });
        });
        dom.analysisContent.querySelectorAll('.analysis-jump-category').forEach((btn) => {
            btn.addEventListener('click', () => {
                showDetalhe(btn.dataset.id);
                dom.analysisResults.style.display = 'none';
            });
        });
        dom.analysisContent.querySelectorAll('.analysis-generate-week-plan').forEach((btn) => {
            btn.addEventListener('click', () => {
                const root = btn.closest('.analysis-ai-practical-next');
                if (!root) return;
                const panel = root.querySelector('.analysis-week-plan');
                if (!panel) return;
                const isOpen = panel.style.display === 'block';
                panel.style.display = isOpen ? 'none' : 'block';
                btn.textContent = isOpen ? '🗓️ Gerar plano de 7 dias' : '🗓️ Ocultar plano de 7 dias';
                btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
                if (!isOpen) refreshWeekPlanPanel(panel);
            });
        });
        dom.analysisContent.querySelectorAll('.analysis-week-plan-day').forEach((input) => {
            input.addEventListener('change', () => {
                const day = input.dataset.day;
                const planKey = input.dataset.planKey;
                if (!day || !planKey) return;
                setWeekPlanState(planKey, day, !!input.checked);
                const panel = input.closest('.analysis-week-plan');
                refreshWeekPlanPanel(panel);
            });
        });
        dom.analysisContent.querySelectorAll('.analysis-week-plan-reset').forEach((btn) => {
            btn.addEventListener('click', () => {
                const panel = btn.closest('.analysis-week-plan');
                if (!panel) return;
                const planKey = panel.dataset.planKey;
                if (!planKey) return;
                resetWeekPlanState(planKey);
                panel.querySelectorAll('.analysis-week-plan-day').forEach((input) => {
                    input.checked = false;
                });
                refreshWeekPlanPanel(panel);
                if (typeof showToast === 'function') {
                    showToast('Plano de 7 dias reiniciado.', 'info');
                }
            });
        });
        // Day 3: documents checklist persistence + reset.
        dom.analysisContent.querySelectorAll('.analysis-ai-docs-item').forEach((input) => {
            input.addEventListener('change', () => {
                const id = input.dataset.docId;
                if (!id) return;
                setDocsChecklistState(id, !!input.checked);
            });
        });
        dom.analysisContent.querySelectorAll('.analysis-ai-docs-reset').forEach((btn) => {
            btn.addEventListener('click', () => {
                resetDocsChecklistState();
                const list = btn.closest('.analysis-ai-docs');
                if (list) {
                    list.querySelectorAll('.analysis-ai-docs-item').forEach((input) => {
                        input.checked = false;
                    });
                }
                if (typeof showToast === 'function') {
                    showToast('Checklist de documentos reiniciada.', 'info');
                }
            });
        });
        dom.analysisContent.querySelectorAll('.analysis-week-plan-copy').forEach((btn) => {
            btn.addEventListener('click', async () => {
                const panel = btn.closest('.analysis-week-plan');
                if (!panel) return;
                const lines = ['Plano de 7 dias — NossoDireito'];
                panel.querySelectorAll('li').forEach((item, index) => {
                    const input = item.querySelector('.analysis-week-plan-day');
                    const checked = input && input.checked;
                    const text = item.querySelector('.analysis-week-plan-text')?.textContent?.trim() || item.textContent.trim();
                    lines.push(`${checked ? '[x]' : '[ ]'} Dia ${index + 1}: ${text}`);
                });
                const payload = lines.join('\n');
                try {
                    await navigator.clipboard.writeText(payload);
                    if (typeof showToast === 'function') {
                        showToast('Plano copiado para a área de transferência.', 'success');
                    }
                } catch {
                    if (typeof showToast === 'function') {
                        showToast('Não foi possível copiar automaticamente. Selecione e copie manualmente.', 'warning');
                    }
                }
            });
        });
        // LGPD Art. 20: human review button toggle
        dom.analysisContent.querySelectorAll('.human-review-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                const info = btn.nextElementSibling;
                if (!info) return;
                const isOpen = info.style.display === 'block';
                info.style.display = isOpen ? 'none' : 'block';
                btn.setAttribute('aria-expanded', String(!isOpen));
            });
        });
    }
    function renderWeekPlan(priorityOrder, titleById) {
        const first = priorityOrder[0] || null;
        const second = priorityOrder[1] || first;
        const third = priorityOrder[2] || second || first;
        const planKey = priorityOrder.join('|') || 'default';
        const state = getWeekPlanState(planKey);

        const label = (id, fallback) => escapeHtml((id && titleById[id]) ? titleById[id] : fallback);
        const checkbox = (day) => state[String(day)] ? 'checked' : '';

        const safeKey = sanitizePlanKey(planKey);
        return `
<div class="analysis-week-plan" style="display:none;" role="group" aria-label="Plano de 7 dias" aria-live="polite" data-plan-key="${escapeHtml(safeKey)}">
  <header class="analysis-week-plan-header">
    <span class="analysis-week-plan-counter" aria-live="polite">0/7 dias concluídos</span>
    <div class="analysis-week-plan-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="Progresso do plano de 7 dias">
      <div class="analysis-week-plan-bar-fill"></div>
    </div>
  </header>
  <ol>
    <li data-day="1"><label><input type="checkbox" class="analysis-week-plan-day" data-day="1" data-plan-key="${escapeHtml(safeKey)}" aria-label="Dia 1" ${checkbox(1)}><span class="analysis-week-plan-text"><strong>Organize</strong> laudo, exames e documentos pessoais em uma pasta única.</span></label></li>
    <li data-day="2"><label><input type="checkbox" class="analysis-week-plan-day" data-day="2" data-plan-key="${escapeHtml(safeKey)}" aria-label="Dia 2" ${checkbox(2)}><span class="analysis-week-plan-text"><strong>Revise</strong> requisitos e próximos passos de <strong>${label(first, '1ª prioridade')}</strong>.</span></label></li>
    <li data-day="3"><label><input type="checkbox" class="analysis-week-plan-day" data-day="3" data-plan-key="${escapeHtml(safeKey)}" aria-label="Dia 3" ${checkbox(3)}><span class="analysis-week-plan-text"><strong>Separe</strong> comprovantes e links oficiais para <strong>${label(first, '1ª prioridade')}</strong>.</span></label></li>
    <li data-day="4"><label><input type="checkbox" class="analysis-week-plan-day" data-day="4" data-plan-key="${escapeHtml(safeKey)}" aria-label="Dia 4" ${checkbox(4)}><span class="analysis-week-plan-text"><strong>Inicie</strong> a solicitação principal de <strong>${label(second, '2ª prioridade')}</strong>.</span></label></li>
    <li data-day="5"><label><input type="checkbox" class="analysis-week-plan-day" data-day="5" data-plan-key="${escapeHtml(safeKey)}" aria-label="Dia 5" ${checkbox(5)}><span class="analysis-week-plan-text"><strong>Faça follow-up</strong> dos protocolos e pendências em <strong>${label(second, '2ª prioridade')}</strong>.</span></label></li>
    <li data-day="6"><label><input type="checkbox" class="analysis-week-plan-day" data-day="6" data-plan-key="${escapeHtml(safeKey)}" aria-label="Dia 6" ${checkbox(6)}><span class="analysis-week-plan-text"><strong>Avance</strong> no processo de <strong>${label(third, '3ª prioridade')}</strong>.</span></label></li>
    <li data-day="7"><label><input type="checkbox" class="analysis-week-plan-day" data-day="7" data-plan-key="${escapeHtml(safeKey)}" aria-label="Dia 7" ${checkbox(7)}><span class="analysis-week-plan-text"><strong>Revise</strong> resultados, pendências e planeje a próxima semana.</span></label></li>
  </ol>
  <div class="analysis-week-plan-actions">
    <button class="btn btn-sm btn-outline analysis-week-plan-copy" type="button">Copiar plano</button>
    <button class="btn btn-sm btn-outline analysis-week-plan-reset" type="button">Reiniciar</button>
  </div>
  <p class="analysis-hint">Mantenha número de protocolo, data e órgão em uma checklist para acelerar retornos.</p>
</div>`;
    }
    function renderAIPracticalSummary(ai, localResults) {
        const aiRights = Array.isArray(ai?.direitos_sugeridos) ? ai.direitos_sugeridos : [];
        const localIds = new Set((Array.isArray(localResults) ? localResults : []).map((r) => r?.category?.id).filter(Boolean));

        // v1.43.26 — Tier 3: dedup mantendo metadados (justificativa, confianca)
        // para alimentar mini-cards inline (desambiguação de sugestões IA).
        const aiSuggestionsById = new Map();
        aiRights.forEach((r) => {
            const catId = String(r?.categoria_id || '').trim();
            if (!catId || aiSuggestionsById.has(catId)) return;
            aiSuggestionsById.set(catId, {
                id: catId,
                justificativa: String(r?.justificativa || '').trim(),
                confianca: String(r?.confianca || 'media').trim().toLowerCase(),
            });
        });
        const aiIds = Array.from(aiSuggestionsById.keys());
        const reinforced = aiIds.filter((id) => localIds.has(id));
        const newFromAI = aiIds.filter((id) => !localIds.has(id));
        const localTop = (Array.isArray(localResults) ? localResults : [])
            .slice(0, 3)
            .map((r) => r?.category?.id)
            .filter(Boolean);
        const priorityOrder = [...newFromAI, ...reinforced, ...localTop]
            .filter((id, idx, arr) => arr.indexOf(id) === idx)
            .slice(0, 3);

        const catById = {};
        const titleById = {};
        if (Array.isArray(direitosData)) {
            direitosData.forEach((cat) => {
                if (cat?.id) {
                    catById[cat.id] = cat;
                    titleById[cat.id] = cat?.titulo || cat.id;
                }
            });
        }

        // v1.43.26 — Tier 3: mini-card inline com justificativa literal da IA
        // (resolve ambiguidade entre múltiplas sugestões competindo).
        const confiancaLabel = (c) => c === 'alta' ? 'Alta confiança' : c === 'baixa' ? 'Baixa confiança' : 'Média confiança';
        const renderSuggestionCard = (id, variant) => {
            const cat = catById[id];
            const titulo = cat?.titulo || titleById[id] || id;
            const resumo = cat?.resumo || '';
            const sug = aiSuggestionsById.get(id) || {};
            const confianca = sug.confianca || 'media';
            const justificativa = sug.justificativa || '';
            const variantClass = variant === 'reinforced' ? 'analysis-ai-suggestion-card--reinforced' : 'analysis-ai-suggestion-card--new';
            const variantLabel = variant === 'reinforced' ? 'Confirmado' : 'Novo';
            return `
<article class="analysis-ai-suggestion-card ${variantClass}" data-cat-id="${escapeHtml(id)}">
  <header class="analysis-ai-suggestion-card__header">
    <div class="analysis-ai-suggestion-card__title">
      <h4>${escapeHtml(titulo)}</h4>
      <div class="analysis-ai-suggestion-card__badges">
        <span class="analysis-ai-suggestion-card__variant">${variantLabel}</span>
        <span class="analysis-ai-suggestion-card__confianca analysis-ai-suggestion-card__confianca--${escapeHtml(confianca)}" aria-label="${confiancaLabel(confianca)}">${confiancaLabel(confianca)}</span>
      </div>
    </div>
  </header>
  ${resumo ? `<p class="analysis-ai-suggestion-card__resumo">${escapeHtml(resumo)}</p>` : ''}
  ${justificativa ? `
  <blockquote class="analysis-ai-suggestion-card__quote" aria-label="Trecho citado do documento que motivou a sugestão">
    <span class="analysis-ai-suggestion-card__quote-label">Trecho do documento citado pela IA:</span>
    <span class="analysis-ai-suggestion-card__quote-text">“${escapeHtml(justificativa)}”</span>
  </blockquote>` : ''}
  <div class="analysis-ai-suggestion-card__actions">
    <button class="btn btn-sm btn-primary analysis-jump-category" data-id="${escapeHtml(id)}" type="button">
      Abrir passo a passo →
    </button>
  </div>
</article>`;
        };

        const renderSuggestionGroup = (ids, variant, emptyText) => {
            if (!ids.length) return `<p class="analysis-hint">${emptyText}</p>`;
            return `<div class="analysis-ai-suggestion-list">${ids.map((id) => renderSuggestionCard(id, variant)).join('')}</div>`;
        };

        const weekPlanHtml = priorityOrder.length
            ? `
<div class="analysis-ai-practical-next">
  <button class="btn btn-sm btn-secondary analysis-generate-week-plan" type="button" aria-expanded="false">
    Gerar plano de 7 dias
  </button>
  ${renderAIDocsChecklist()}
  ${renderWeekPlan(priorityOrder, titleById)}
  <p class="analysis-ai-disclaimer"><strong>⚠️ Importante:</strong> esta sugestão de IA é informativa, baseada em fontes oficiais já indexadas pelo catálogo, e <strong>não substitui</strong> parecer profissional. A confirmação de elegibilidade cabe à <strong>Defensoria Pública</strong> (CF Art. 134) ou ao <strong>CRAS</strong> (Lei 8.742/1993) da sua cidade.</p>
</div>`
            : '';

        return `
<div class="analysis-ai-practical" role="region" aria-label="Resumo prático do que mudou com IA">
  <h3>O que mudou com IA</h3>
  <p class="analysis-ai-practical-intro">Cada sugestão da IA mostra o <strong>trecho literal do seu documento</strong> que motivou a indicação — ajuda você a comparar e escolher antes de abrir o passo a passo.</p>
  <div class="analysis-ai-practical-section">
    <strong class="analysis-ai-practical-section__label">Direitos confirmados pela IA (já detectados localmente)</strong>
    ${renderSuggestionGroup(reinforced, 'reinforced', 'A IA não trouxe confirmações adicionais sobre os direitos já detectados localmente.')}
  </div>
  <div class="analysis-ai-practical-section">
    <strong class="analysis-ai-practical-section__label">Novos direitos sugeridos pela IA</strong>
    ${renderSuggestionGroup(newFromAI, 'new', 'A IA não sugeriu novos direitos além dos já detectados localmente.')}
  </div>
  ${weekPlanHtml}
</div>`;
    }
    // ── Análise IA: consentimento LGPD + chamada ao backend + renderização ──
    // v2: chave bumpada na migração para Azure OpenAI (v1.18.0) — invalida consentimentos
    // legados dados ao antigo provedor Doc Intelligence (mudança de base legal LGPD).
    const AI_CONSENT_KEY = 'nd_ai_consent_v2';
    const AI_CONSENT_TTL_MS = 30 * 24 * 60 * 60 * 1000; // 30 dias
    const WEEK_PLAN_STORAGE_KEY = 'nd_ai_week_plan_v1';
    let storageWriteWarningShown = false;

    function notifyStorageWriteFailure() {
        if (storageWriteWarningShown) return;
        storageWriteWarningShown = true;
        if (typeof showToast === 'function') {
            showToast('Não foi possível salvar no navegador. Algumas preferências não serão persistidas.', 'warning');
        }
    }

    function getStoredWeekPlans() {
        try {
            const raw = localStorage.getItem(WEEK_PLAN_STORAGE_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch {
            return {};
        }
    }

    function getWeekPlanState(planKey) {
        const allPlans = getStoredWeekPlans();
        return allPlans[planKey] || {};
    }

    // Day 6: hard cap to prevent unbounded growth of localStorage entries.
    const WEEK_PLAN_MAX_KEYS = 20;
    function sanitizePlanKey(planKey) {
        if (typeof planKey !== 'string') return 'default';
        // Allow only category-id chars + the pipe separator used by priorityOrder.join('|').
        const clean = planKey.replace(/[^a-zA-Z0-9_\-|]/g, '').slice(0, 200);
        return clean || 'default';
    }
    function pruneStoredWeekPlans(allPlans) {
        const keys = Object.keys(allPlans);
        if (keys.length <= WEEK_PLAN_MAX_KEYS) return allPlans;
        // Drop oldest insertion-order keys (object key order is insertion-ordered in JS).
        const toDrop = keys.slice(0, keys.length - WEEK_PLAN_MAX_KEYS);
        toDrop.forEach((k) => { delete allPlans[k]; });
        return allPlans;
    }

    function setWeekPlanState(planKey, day, done) {
        try {
            const safeKey = sanitizePlanKey(planKey);
            const allPlans = getStoredWeekPlans();
            const current = allPlans[safeKey] || {};
            current[String(day)] = !!done;
            allPlans[safeKey] = current;
            pruneStoredWeekPlans(allPlans);
            localStorage.setItem(WEEK_PLAN_STORAGE_KEY, JSON.stringify(allPlans));
        } catch {
            notifyStorageWriteFailure();
        }
    }

    function resetWeekPlanState(planKey) {
        try {
            const allPlans = getStoredWeekPlans();
            allPlans[planKey] = {};
            localStorage.setItem(WEEK_PLAN_STORAGE_KEY, JSON.stringify(allPlans));
        } catch {
            notifyStorageWriteFailure();
        }
    }

    function updateWeekPlanCompletedStyles(panel) {
        panel.querySelectorAll('.analysis-week-plan-day').forEach((input) => {
            const item = input.closest('li');
            if (!item) return;
            item.classList.toggle('completed', !!input.checked);
            input.setAttribute('aria-checked', input.checked ? 'true' : 'false');
        });
    }

    // Day 2: progress counter + bar reflecting completed/total days.
    function updateWeekPlanProgress(panel) {
        const inputs = panel.querySelectorAll('.analysis-week-plan-day');
        const total = inputs.length || 7;
        let done = 0;
        inputs.forEach((i) => { if (i.checked) done += 1; });
        const pct = Math.round((done / total) * 100);
        const counter = panel.querySelector('.analysis-week-plan-counter');
        if (counter) counter.textContent = `${done}/${total} dias concluídos`;
        const bar = panel.querySelector('.analysis-week-plan-bar-fill');
        if (bar) {
            bar.style.width = `${pct}%`;
            const barWrap = panel.querySelector('.analysis-week-plan-bar');
            if (barWrap) barWrap.setAttribute('aria-valuenow', String(pct));
        }
    }

    // Day 2: highlight the first unchecked day as "focus now".
    function updateWeekPlanCurrentDay(panel) {
        const items = panel.querySelectorAll('li[data-day]');
        let marked = false;
        items.forEach((li) => {
            const input = li.querySelector('.analysis-week-plan-day');
            const isCurrent = !marked && input && !input.checked;
            li.classList.toggle('current', !!isCurrent);
            if (isCurrent) marked = true;
        });
    }

    function refreshWeekPlanPanel(panel) {
        if (!panel) return;
        updateWeekPlanCompletedStyles(panel);
        updateWeekPlanProgress(panel);
        updateWeekPlanCurrentDay(panel);
    }

    // Day 3: "Documentos essenciais" checklist (independent persistence).
    const DOCS_CHECKLIST_KEY = 'nd_ai_docs_checklist_v1';
    const DOCS_CHECKLIST_ITEMS = [
        { id: 'laudo',     label: 'Laudo médico atualizado (≤2 anos) com CID descrito' },
        { id: 'cpf_rg',    label: 'CPF e RG (cópia legível)' },
        { id: 'residencia',label: 'Comprovante de residência recente (≤3 meses)' },
        { id: 'renda',     label: 'Comprovante de renda familiar (últimos 3 meses)' },
        { id: 'ciptea',    label: 'Carteirinha CIPTEA, quando aplicável' },
        { id: 'responsavel', label: 'Documentos do responsável legal, se aplicável' },
    ];
    function getDocsChecklistState() {
        try {
            const raw = localStorage.getItem(DOCS_CHECKLIST_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch { return {}; }
    }
    function setDocsChecklistState(id, done) {
        try {
            const cur = getDocsChecklistState();
            cur[id] = !!done;
            localStorage.setItem(DOCS_CHECKLIST_KEY, JSON.stringify(cur));
        } catch {
            notifyStorageWriteFailure();
        }
    }
    function resetDocsChecklistState() {
        try {
            localStorage.setItem(DOCS_CHECKLIST_KEY, '{}');
        } catch {
            notifyStorageWriteFailure();
        }
    }
    function renderAIDocsChecklist() {
        const state = getDocsChecklistState();
        const items = DOCS_CHECKLIST_ITEMS.map((it) => {
            const checked = state[it.id] ? 'checked' : '';
            return `<li><label><input type="checkbox" class="analysis-ai-docs-item" data-doc-id="${escapeHtml(it.id)}" ${checked}><span class="analysis-ai-docs-text">${escapeHtml(it.label)}</span></label></li>`;
        }).join('');
        return `
<details class="analysis-ai-docs" role="group" aria-label="Documentos essenciais para pedir benefícios">
  <summary>Documentos essenciais (clique para abrir)</summary>
  <ul>${items}</ul>
  <div class="analysis-ai-docs-actions">
    <button class="btn btn-sm btn-outline analysis-ai-docs-reset" type="button">Reiniciar lista</button>
  </div>
  <p class="analysis-hint">Salvo no seu navegador (LGPD: nada é enviado). Reaproveite em todos os pedidos.</p>
</details>`;
    }
    function emitAIConsentChanged() {
        document.dispatchEvent(new Event('ai-consent-changed'));
    }
    function getStoredAIConsentMeta() {
        try {
            const raw = localStorage.getItem(AI_CONSENT_KEY);
            if (!raw) return { granted: false, remainingDays: 0, exp: 0 };
            const { granted, exp } = JSON.parse(raw);
            const expTs = Number(exp);
            if (!granted || !Number.isFinite(expTs)) {
                return { granted: false, remainingDays: 0, exp: 0 };
            }
            const remainingMs = expTs - Date.now();
            if (remainingMs <= 0) {
                return { granted: false, remainingDays: 0, exp: expTs };
            }
            const remainingDays = Math.max(1, Math.ceil(remainingMs / 86400000));
            return { granted: true, remainingDays, exp: expTs };
        } catch {
            return { granted: false, remainingDays: 0, exp: 0 };
        }
    }
    function getStoredAIConsent() {
        return getStoredAIConsentMeta().granted;
    }
    function setStoredAIConsent(granted, sensitive) {
        try {
            localStorage.setItem(AI_CONSENT_KEY, JSON.stringify({
                granted: !!granted,
                sensitive: !!sensitive,
                exp: Date.now() + AI_CONSENT_TTL_MS,
            }));
            emitAIConsentChanged();
        } catch {
            notifyStorageWriteFailure();
        }
    }
    function getAIConsent() {
        if (getStoredAIConsent()) return Promise.resolve(true);
        const modal = document.getElementById('aiConsentModal');
        const btnAccept = document.getElementById('aiConsentAccept');
        const btnCancel = document.getElementById('aiConsentCancel');
        const cbRemember = document.getElementById('aiConsentRemember');
        const cbSensitive = document.getElementById('aiConsentSensitive');
        if (!modal || !btnAccept || !btnCancel) {
            return Promise.resolve(window.confirm(
                'Permitir envio do texto anonimizado (que pode conter dados de saúde) '
                + 'para análise com IA (Azure OpenAI gpt-4o-mini, Brasil Sul)? '
                + 'Art. 11 LGPD: consentimento específico para dados sensíveis.'
            ));
        }
        if (modal.style.display === 'flex') return Promise.resolve(false);
        modal.style.display = 'flex';
        if (cbRemember) cbRemember.checked = false;
        if (cbSensitive) {
            cbSensitive.checked = false;
            btnAccept.disabled = true;
            btnAccept.setAttribute('aria-disabled', 'true');
        }
        return new Promise((resolve) => {
            const cleanup = (result) => {
                modal.style.display = 'none';
                btnAccept.removeEventListener('click', onAccept);
                btnCancel.removeEventListener('click', onCancel);
                if (cbSensitive) cbSensitive.removeEventListener('change', onSensitiveChange);
                document.removeEventListener('keydown', onKey);
                resolve(result);
            };
            const onSensitiveChange = () => {
                const checked = cbSensitive.checked;
                btnAccept.disabled = !checked;
                btnAccept.setAttribute('aria-disabled', String(!checked));
            };
            const onAccept = () => {
                if (cbSensitive && !cbSensitive.checked) return;
                if (cbRemember && cbRemember.checked) {
                    setStoredAIConsent(true, !!(cbSensitive && cbSensitive.checked));
                }
                cleanup(true);
            };
            const onCancel = () => cleanup(false);
            // 1.37.0: botao "Revogar" foi removido do modal — por definicao,
            // este modal so abre quando nao ha consentimento salvo. Revogacao
            // vive nos paineis permanentes da secao LGPD (cadeado dinamico).
            const onKey = (e) => { if (e.key === 'Escape') cleanup(false); };
            btnAccept.addEventListener('click', onAccept);
            btnCancel.addEventListener('click', onCancel);
            if (cbSensitive) cbSensitive.addEventListener('change', onSensitiveChange);
            document.addEventListener('keydown', onKey);
            setTimeout(() => btnAccept.focus(), 50);
        });
    }
    // LGPD Art. 8º §5 — exposição global para chamada via console / outros pontos do UI
    window.revokeAIConsent = function () {
        try {
            localStorage.removeItem(AI_CONSENT_KEY);
            emitAIConsentChanged();
            return true;
        } catch {
            return false;
        }
    };
    async function callServerAnalysis(anonymizedText) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 15000);
        let resp;
        try {
            resp = await fetch('/api/analyze-document', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
                body: JSON.stringify({ text: anonymizedText }),
                signal: controller.signal,
            });
        } catch (err) {
            if (err && err.name === 'AbortError') {
                throw new Error('Tempo limite excedido na análise IA.');
            }
            throw err;
        } finally {
            clearTimeout(timeout);
        }
        const ctype = resp.headers.get('content-type') || '';
        const body = ctype.includes('application/json') ? await resp.json().catch(() => ({})) : { error: await resp.text().catch(() => '') };
        if (!resp.ok) {
            const msg = body.error || body.message || `HTTP ${resp.status}`;
            if (resp.status === 503) throw new Error('Análise IA indisponível no servidor (AI_ANALYSIS_ENABLED desativado).');
            if (resp.status === 413) throw new Error('Texto muito grande para análise (máx. 200KB).');
            if (resp.status === 422) throw new Error('Detectado PII residual no texto anonimizado — envio bloqueado por segurança.');
            if (resp.status === 502 || resp.status === 504) throw new Error('Falha na comunicação com o Azure OpenAI.');
            throw new Error(msg);
        }
        return body;
    }
    function isValidCID(code) {
        // CID-10: letra + 2 dígitos + opcional .N ou .NN
        return /^[A-Z]\d{2}(\.\d{1,2})?$/.test(String(code || '').trim());
    }

    // ── Revisão humana (LGPD Art. 20) ──
    function renderHumanReviewButton() {
        return `<div class="analysis-human-review" role="region" aria-labelledby="humanReviewTitle">
<h4 id="humanReviewTitle">Direito à revisão humana (LGPD Art. 20)</h4>
<p>Você pode pedir que uma pessoa revise como a <strong>IA processou seu documento</strong> nesta ferramenta (CIDs detectados, datas, direitos sugeridos).</p>
<p class="human-review-scope"><small><strong>Escopo:</strong> este canal trata apenas do <strong>funcionamento automatizado do site</strong>. Não é para questionar leis, direitos ou conteúdo do catálogo — esses vêm de fontes oficiais (gov.br) e dúvidas jurídicas devem ser levadas à Defensoria Pública ou advogado.</small></p>
<button class="btn btn-outline human-review-btn" type="button"
  aria-describedby="humanReviewTitle">
  Pedir revisão humana
</button>
<div class="human-review-info" style="display:none;" aria-live="polite">
<p>Envie um e-mail para
<a href="mailto:dpo@fabiotreze.com?subject=Revisão humana — Art. 20 LGPD">dpo@fabiotreze.com</a>
com o assunto <strong>"Revisão humana — Art. 20 LGPD"</strong> descrevendo o que a IA processou de forma incorreta (ex.: CID errado, data confundida, direito sugerido sem base no texto).</p>
<p>Prazo de resposta: até 15 dias corridos.</p>
<p><small>Nenhum dado pessoal é enviado automaticamente. Você decide o que incluir no e-mail.</small></p>
</div>
</div>`;
    }

    function renderAIResult(ai) {
        // v1.18.0: novo schema do Azure OpenAI gpt-4o-mini (vs. legacy Doc Intelligence)
        const cids = Array.isArray(ai.cids) ? ai.cids : [];
        const datas = Array.isArray(ai.datas) ? ai.datas : [];
        const diagnosticos = Array.isArray(ai.diagnosticos) ? ai.diagnosticos : [];
        const direitos = Array.isArray(ai.direitos_sugeridos) ? ai.direitos_sugeridos : [];
        const resumo = String(ai.resumo || '').trim();
        const confiancaGeral = String(ai.confianca || 'baixa');
        const tokensIn = (ai.tokens && ai.tokens.input) || 0;
        const tokensOut = (ai.tokens && ai.tokens.output) || 0;
        const confBadgeClass = (c) => c === 'alta' ? 'high' : (c === 'media' ? 'mid' : 'low');
        const confBadgeIcon = (c) => c === 'alta' ? '✓' : (c === 'media' ? '~' : '⚠');
        const cidBadges = cids.length
            ? cids.map((c) => {
                const code = String(c.codigo || c).trim();
                const ok = isValidCID(code);
                const conf = String(c.confianca || 'baixa');
                const desc = escapeHtml(c.descricao || '');
                return `<span class="kw-tag ${ok ? confBadgeClass(conf) : 'low'}" title="${desc} (confiança: ${conf})">${ok ? confBadgeIcon(conf) : '⚠'} ${escapeHtml(code)}${desc ? ' — ' + desc : ''}</span>`;
            }).join(' ')
            : '<span class="analysis-hint">Nenhum CID identificado pelo modelo.</span>';
        const dateBadges = datas.length
            ? datas.slice(0, 8).map((d) => {
                const data = escapeHtml(d.data || '');
                const ctx = escapeHtml(d.contexto || '');
                return `<span class="kw-tag mid" title="${ctx}">${data}${ctx ? ' — ' + ctx : ''}</span>`;
            }).join(' ')
            : '<span class="analysis-hint">Nenhuma data relevante identificada.</span>';
        const diagBadges = diagnosticos.length
            ? diagnosticos.slice(0, 8).map((d) => `<li>${escapeHtml(d)}</li>`).join('')
            : '<li class="analysis-hint">Nenhum diagnóstico explicitado no texto.</li>';
        const direitosHtml = direitos.length
            ? direitos.map((r) => {
                const cat = escapeHtml(r.categoria_id || '');
                const just = escapeHtml(r.justificativa || '');
                const conf = String(r.confianca || 'baixa');
                return `<li><span class="kw-tag ${confBadgeClass(conf)}">${confBadgeIcon(conf)} ${cat}</span> — ${just}</li>`;
            }).join('')
            : '<li class="analysis-hint">Nenhum direito sugerido pelo modelo.</li>';
        return `
<div class="analysis-ai-section" style="margin-top:18px;padding:16px;border:1px solid #cfe2ff;background:#f5faff;border-radius:6px;">
  <h3 style="margin-top:0;">Análise por IA (Azure OpenAI gpt-4o-mini — Brasil Sul)</h3>
  <p style="font-size:0.85rem;color:#555;margin:4px 0 12px;">
    Texto enviado de forma <strong>anonimizada</strong>. Confiança geral: <strong>${escapeHtml(confiancaGeral)}</strong>. Tokens: ${tokensIn}→${tokensOut}.
  </p>
  ${resumo ? `<div style="background:#fff;padding:10px;border-left:3px solid #0d6efd;border-radius:4px;margin-bottom:12px;"><strong>Resumo orientativo:</strong><br>${escapeHtml(resumo)}</div>` : ''}
  <div style="margin-bottom:10px;">
    <strong>CIDs identificados:</strong><br>
    ${cidBadges}
  </div>
  <div style="margin-bottom:10px;">
    <strong>Datas relevantes:</strong><br>
    ${dateBadges}
  </div>
  <div style="margin-bottom:10px;">
    <strong>Diagnósticos identificados:</strong>
    <ul style="margin:4px 0 0 20px;">${diagBadges}</ul>
  </div>
  <div style="margin-bottom:10px;">
    <strong>Direitos sugeridos:</strong>
    <ul style="margin:4px 0 0 20px;">${direitosHtml}</ul>
  </div>
  <p style="font-size:0.8rem;color:#666;margin:10px 0 0;">
    ✓ = alta confiança · ~ = média · ⚠ = baixa/suspeito. <strong>Não substitui</strong> orientação profissional.
  </p>
</div>`;
    }
    async function getCryptoKey() {
        if (!CRYPTO_AVAILABLE) return null;
        const db = await openDB();
        try {
            const existing = await new Promise((resolve, reject) => {
                const tx = db.transaction(CRYPTO_STORE, 'readonly');
                const req = tx.objectStore(CRYPTO_STORE).get(CRYPTO_KEY_ID);
                req.onsuccess = () => resolve(req.result);
                req.onerror = () => reject(req.error);
            });
            if (existing && existing.key) {
                return existing.key;
            }
            if (existing && existing.jwk) {
                return await crypto.subtle.importKey(
                    'jwk', existing.jwk,
                    { name: 'AES-GCM', length: 256 },
                    false, ['encrypt', 'decrypt']
                );
            }
        } finally {
            db.close();
        }
        let key;
        try {
            key = await crypto.subtle.generateKey(
                { name: 'AES-GCM', length: 256 },
                false,
                ['encrypt', 'decrypt']
            );
            const testDb = await openDB();
            try {
                await new Promise((resolve, reject) => {
                    const tx = testDb.transaction(CRYPTO_STORE, 'readwrite');
                    tx.objectStore(CRYPTO_STORE).put({ id: CRYPTO_KEY_ID, key: key });
                    tx.oncomplete = () => resolve();
                    tx.onerror = () => reject(tx.error);
                });
            } finally {
                testDb.close();
            }
            return key;
        } catch (cloneErr) {
            console.warn('[Crypto] CryptoKey structured clone failed, using JWK fallback:', cloneErr.message);
            // exportable forçado a true via flag em generateKey abaixo (JWK export path)
            key = await crypto.subtle.generateKey(
                { name: 'AES-GCM', length: 256 },
                true,
                ['encrypt', 'decrypt']
            );
        }
        const jwk = await crypto.subtle.exportKey('jwk', key);
        const db2 = await openDB();
        try {
            await new Promise((resolve, reject) => {
                const tx = db2.transaction(CRYPTO_STORE, 'readwrite');
                tx.objectStore(CRYPTO_STORE).put({ id: CRYPTO_KEY_ID, jwk: jwk });
                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            });
        } finally {
            db2.close();
        }
        return key;
    }
    async function encryptBuffer(plainBuffer) {
        const key = await getCryptoKey();
        if (!key) {
            return { ciphertext: plainBuffer, iv: null };
        }
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const ciphertext = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv, tagLength: 128 },
            key,
            plainBuffer
        );
        return { ciphertext, iv: Array.from(iv) };
    }
    async function decryptFileData(fileObj) {
        if (!fileObj.encrypted || !fileObj.iv) {
            return fileObj.data;
        }
        const key = await getCryptoKey();
        if (!key) {
            console.warn('Crypto unavailable — returning raw data');
            return fileObj.data;
        }
        try {
            const iv = new Uint8Array(fileObj.iv);
            return await crypto.subtle.decrypt(
                { name: 'AES-GCM', iv: iv, tagLength: 128 },
                key,
                fileObj.data
            );
        } catch (err) {
            console.error('Decryption failed:', err);
            showToast('Falha ao descriptografar arquivo. O arquivo pode estar corrompido.', 'error');
            return null;
        }
    }
    async function cleanupExpiredFiles() {
        try {
            const files = await getAllFiles();
            const now = Date.now();
            let removed = 0;
            for (const file of files) {
                if (file.expiresAt && new Date(file.expiresAt).getTime() < now) {
                    await deleteFile(file.id);
                    removed++;
                }
            }
            if (removed > 0) {
                console.info(`[Security] ${removed} arquivo(s) expirado(s) removido(s) automaticamente.`);
            }
            return removed;
        } catch (err) {
            console.error('Erro na limpeza de arquivos expirados:', err);
            return 0;
        }
    }
    function openDB() {
        return new Promise((resolve, reject) => {
            // Firefox private browsing has 0-byte IndexedDB quota — detect & warn
            if (typeof indexedDB === 'undefined') {
                return reject(new Error('IndexedDB not available'));
            }
            let req;
            try {
                req = indexedDB.open(DB_NAME, DB_VERSION);
            } catch (e) {
                return reject(e); // SecurityError in some private-mode browsers
            }
            req.onupgradeneeded = (e) => {
                const db = e.target.result;
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME, { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains(CRYPTO_STORE)) {
                    db.createObjectStore(CRYPTO_STORE, { keyPath: 'id' });
                }
            };
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
            req.onblocked = () => reject(new Error('IndexedDB blocked by another tab'));
        });
    }
    async function dbOp(mode, fn) {
        const db = await openDB();
        return new Promise((ok, no) => {
            const tx = db.transaction(STORE_NAME, mode);
            const r = fn(tx.objectStore(STORE_NAME));
            tx.oncomplete = () => { db.close(); ok(r.result); };
            tx.onerror = () => { db.close(); no(tx.error); };
        });
    }
    function storeFile(f) { return dbOp('readwrite', s => s.put(f)); }
    function getAllFiles() { return dbOp('readonly', s => s.getAll()); }
    function getFile(id) { return dbOp('readonly', s => s.get(id)); }
    function deleteFile(id) { return dbOp('readwrite', s => s.delete(id)); }
    function clearAllFiles() { return dbOp('readwrite', s => s.clear()); }
    function getFileCount() { return dbOp('readonly', s => s.count()); }
    function setupFooter() {
        if (dom.lastUpdate && !dom.lastUpdate.textContent) {
            dom.lastUpdate.textContent = new Date().toLocaleDateString('pt-BR');
        }
    }
    function setupFooterVersion() {
        if (dom.footerVersion && jsonMeta && jsonMeta.versao) {
            dom.footerVersion.textContent = `v${jsonMeta.versao}`;
            dom.footerVersion.title = `Versão dos dados: ${jsonMeta.versao}`;
        }
        if (dom.dataAviso && jsonMeta && jsonMeta.aviso) {
            const small = dom.dataAviso.querySelector('small') || dom.dataAviso;
            small.textContent = jsonMeta.aviso;
        }
    }
    function localGet(key) {
        try {
            const val = localStorage.getItem(STORAGE_PREFIX + key);
            return val ? safeJsonParse(val) : null;
        } catch {
            return null;
        }
    }
    function localSet(key, value) {
        try {
            localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
        } catch {
        }
    }
    function isSafeUrl(url) {
        if (!url || typeof url !== 'string') return false;
        const trimmed = url.trim().toLowerCase();
        // Bloqueia esquemas perigosos: javascript:, vbscript:, data: (XSS via data:text/html)
        if (trimmed.startsWith('javascript:') || trimmed.startsWith('vbscript:') || trimmed.startsWith('data:')) return false;
        if (trimmed.startsWith('#') || trimmed.startsWith('/') || trimmed.startsWith('./')) return true;
        if (trimmed.startsWith('blob:') || trimmed.startsWith('tel:') || trimmed.startsWith('mailto:')) return true;
        try {
            const parsed = new URL(url, window.location.origin);
            if (parsed.origin === window.location.origin) return true;
            const host = parsed.hostname;
            const TRUSTED = [
                '.gov.br', '.planalto.gov.br', '.inss.gov.br', '.mds.gov.br',
                '.apaebrasil.org.br', '.ama.org.br', 'cdnjs.cloudflare.com',
                '.oab.org.br', '.cnmp.mp.br', '.anadep.org.br', '.mp.br',
                '.ijc.org.br', '.procon.sp.gov.br', '.autismbrasil.org',
                '.abntcatalogo.com.br', '.caixa.gov.br',
                '.cfm.org.br', '.cfp.org.br', '.who.int',
            ];
            return TRUSTED.some(t => host === t.slice(1) || host.endsWith(t));
        } catch {
            return false;
        }
    }
    const _escapeDiv = document.createElement('div');
    function escapeHtml(str) {
        if (!str) return '';
        if (typeof str !== 'string') str = String(str);
        _escapeDiv.textContent = str;
        return _escapeDiv.innerHTML;
    }
    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    function normalizeText(text) {
        if (typeof text !== 'string') return '';
        return text
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '');
    }
    function formatDate(dateStr) {
        try {
            const d = new Date(dateStr.includes('T') ? dateStr : dateStr + 'T00:00:00');
            return d.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'long',
                year: 'numeric',
            });
        } catch {
            return dateStr;
        }
    }
    function formatBytes(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
    function formatTimeRemaining(expiresAt) {
        const diff = new Date(expiresAt).getTime() - Date.now();
        if (diff <= 0) return 'Expirado';
        const mins = Math.ceil(diff / 60000);
        if (mins < 60) return `Expira em ${mins} min`;
        const hours = Math.floor(mins / 60);
        const remMins = mins % 60;
        return `Expira em ${hours}h${remMins > 0 ? remMins + 'min' : ''}`;
    }
    function setupBackToTop() {
        const btn = document.getElementById('backToTop');
        if (!btn) return;
        let _bttTicking = false;
        window.addEventListener('scroll', () => {
            if (_bttTicking) return;
            _bttTicking = true;
            requestAnimationFrame(() => {
                btn.classList.toggle('visible', window.scrollY > 300);
                _bttTicking = false;
            });
        }, { passive: true });
        btn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    // v1.18.2 — Gerenciador permanente de consentimento IA (LGPD Art. 8º §5).
    // Botão sempre visível na seção LGPD; revoga consentimento armazenado.
    function setupAIConsentManager() {
        const btn = document.getElementById('aiConsentRevokeInline');
        const status = document.getElementById('aiConsentStatus');
        if (!btn || !status) return;
        const animateStatusBadge = () => {
            status.classList.remove('ai-consent-status-badge--updated');
            // Restart animation class reliably on repeated state updates.
            void status.offsetWidth;
            status.classList.add('ai-consent-status-badge--updated');
            setTimeout(() => status.classList.remove('ai-consent-status-badge--updated'), 260);
        };
        const render = () => {
            const consent = getStoredAIConsentMeta();
            status.classList.remove('ai-consent-status-badge--active', 'ai-consent-status-badge--inactive');
            if (consent.granted) {
                const diaLabel = consent.remainingDays === 1 ? 'dia' : 'dias';
                status.textContent = `Ativo - faltam ${consent.remainingDays} ${diaLabel}`;
                status.classList.add('ai-consent-status-badge--active');
                btn.disabled = false;
                btn.textContent = 'Revogar consentimento de IA';
            } else {
                status.textContent = 'Nao armazenado';
                status.classList.add('ai-consent-status-badge--inactive');
                btn.disabled = true;
                btn.textContent = 'Nenhum consentimento ativo';
            }
            animateStatusBadge();
        };
        btn.addEventListener('click', () => {
            const granted = getStoredAIConsent();
            if (!granted) {
                if (typeof showToast === 'function') {
                    showToast('Nenhum consentimento salvo no momento. Ele será solicitado na próxima análise com IA.', 'info');
                }
                render();
                return;
            }
            const ok = window.revokeAIConsent && window.revokeAIConsent();
            if (typeof showToast === 'function') {
                showToast(
                    ok
                        ? 'Consentimento de IA revogado. Será solicitado novamente na próxima análise.'
                        : 'Não foi possível revogar (localStorage indisponível).',
                    ok ? 'info' : 'warning'
                );
            }
            render();
        });
        document.addEventListener('ai-consent-changed', render);
        render();
    }
    // v1.43.43 — Status informativo de consentimento IA no painel da Consulta.
    // ANTES (v1.43.41): expunha botão duplicado de revogar (#aiConsentRevokeQuick),
    // criando 3 caminhos para a mesma ação (aqui + #aiConsentManager + /historico-aceite).
    // AGORA: badge somente-leitura + link contextual para o gerenciador central.
    // Reduz fadiga de decisão e elimina divergência de cópia entre painéis.
    function setupAIConsentQuickStatus() {
        const status = document.getElementById('aiConsentQuickStatus');
        if (!status) return;
        const animateStatusBadge = () => {
            status.classList.remove('ai-consent-status-badge--updated');
            void status.offsetWidth;
            status.classList.add('ai-consent-status-badge--updated');
            setTimeout(() => status.classList.remove('ai-consent-status-badge--updated'), 260);
        };
        const render = () => {
            const consent = getStoredAIConsentMeta();
            status.classList.remove('ai-consent-status-badge--active', 'ai-consent-status-badge--inactive');
            if (consent.granted) {
                const diaLabel = consent.remainingDays === 1 ? 'dia' : 'dias';
                status.textContent = `Consentimento ativo - faltam ${consent.remainingDays} ${diaLabel}`;
                status.classList.add('ai-consent-status-badge--active');
            } else {
                status.textContent = 'Nenhum consentimento salvo';
                status.classList.add('ai-consent-status-badge--inactive');
            }
            animateStatusBadge();
        };
        document.addEventListener('ai-consent-changed', render);
        render();
    }
    // v1.43.16 — Consolidado em setupReferenciasTabs (doc-level handler).
    // Mantida apenas para compatibilidade (no-op).
    function setupNavAvisoScroll() { /* deprecated v1.43.16 */ }

    // ---------- Central de Referências (tabs ARIA) ----------
    // Mapa: hash → tab id. Cobre anchors antigas para preservar compatibilidade.
    const REFERENCIAS_HASH_MAP = {
        '#links': 'referenciasTab-links',
        '#classificacao': 'referenciasTab-classificacao',
        '#orgaos-estaduais': 'referenciasTab-orgaos-estaduais',
        '#instituicoes': 'referenciasTab-instituicoes',
        '#transparencia': 'referenciasTab-transparencia',
        '#disclaimerInline': 'referenciasTab-transparencia',
        '#compromissoAtualizacao': 'referenciasTab-transparencia',
    };

    function activateReferenciasTabByHash(hash) {
        const tabId = REFERENCIAS_HASH_MAP[hash];
        if (!tabId) return false;
        const tab = document.getElementById(tabId);
        if (!tab) return false;
        const tabs = Array.from(document.querySelectorAll('#referenciasTabs .referencias-tab'));
        const idx = tabs.indexOf(tab);
        if (idx < 0) return false;
        activateReferenciasTab(tabs, idx, { focus: false, scroll: false });
        return true;
    }

    function activateReferenciasTab(tabs, idx, { focus = false, scroll = false } = {}) {
        tabs.forEach((t, i) => {
            const selected = i === idx;
            t.setAttribute('aria-selected', selected ? 'true' : 'false');
            t.setAttribute('tabindex', selected ? '0' : '-1');
            const panelId = t.getAttribute('aria-controls');
            const panel = panelId ? document.getElementById(panelId) : null;
            if (panel) {
                if (selected) panel.removeAttribute('hidden');
                else panel.setAttribute('hidden', '');
            }
        });
        if (focus) tabs[idx].focus();
        if (scroll) {
            const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            const wrapper = document.getElementById('referencias');
            if (wrapper) wrapper.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
        }
    }

    function setupReferenciasTabs() {
        const tablist = document.getElementById('referenciasTabs');
        if (!tablist) return;
        const tabs = Array.from(tablist.querySelectorAll('.referencias-tab'));
        if (!tabs.length) return;

        tabs.forEach((tab, i) => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                activateReferenciasTab(tabs, i, { focus: false, scroll: false });
            });
            tab.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    const next = (i + 1) % tabs.length;
                    activateReferenciasTab(tabs, next, { focus: true });
                } else if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    const prev = (i - 1 + tabs.length) % tabs.length;
                    activateReferenciasTab(tabs, prev, { focus: true });
                } else if (e.key === 'Home') {
                    e.preventDefault();
                    activateReferenciasTab(tabs, 0, { focus: true });
                } else if (e.key === 'End') {
                    e.preventDefault();
                    activateReferenciasTab(tabs, tabs.length - 1, { focus: true });
                }
            });
        });

        // Compatibilidade com anchors antigas (#links, #classificacao etc.)
        function syncFromHash() {
            const hash = window.location.hash;
            if (!hash) return;
            activateReferenciasTabByHash(hash);
        }
        window.addEventListener('hashchange', syncFromHash);
        // Initial sync (caso a página abra direto em /#orgaos-estaduais etc.)
        syncFromHash();

        // v1.43.16: handler unificado para QUALQUER link cujo href esteja em
        // REFERENCIAS_HASH_MAP (Apoio top-level, Aviso top-level, todos os
        // subitens do submenu Referências, links do footer, etc.).
        //
        // Fluxo: e.preventDefault → fecha drawer mobile → ativa a tab correta
        // → atualiza hash → aguarda 2 frames (rAF duplo) para o layout do
        // painel recém-revelado ser computado → scrollIntoView (que respeita
        // scroll-padding-top: 80px do <html>, alinhando consistentemente com
        // todos os outros anchors do nav).
        document.addEventListener('click', (e) => {
            const link = e.target instanceof Element ? e.target.closest('a[href^="#"]') : null;
            if (!link) return;
            const hash = link.getAttribute('href');
            if (!hash || !(hash in REFERENCIAS_HASH_MAP)) return;
            const target = document.querySelector(hash);
            if (!target) return;
            e.preventDefault();
            // Fecha drawer mobile do nav, se aberto
            const drawer = document.getElementById('navLinks');
            const toggle = document.getElementById('menuToggle');
            if (drawer && drawer.classList.contains('open')) {
                drawer.classList.remove('open');
                if (toggle) {
                    toggle.classList.remove('open');
                    toggle.setAttribute('aria-expanded', 'false');
                    toggle.setAttribute('aria-label', 'Abrir menu');
                }
            }
            activateReferenciasTabByHash(hash);
            if (history.replaceState) history.replaceState(null, '', hash);
            const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    target.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
                });
            });
        });
    }

    // v1.43.22 — setupNavSubmenu REMOVIDO. O <details> "Referências ▾" foi
    // substituído por links diretos no header (pills). Não há mais submenu
    // a controlar (abertura, esc, click fora, fechamento ao navegar).

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => { init(); setupNavAvisoScroll(); setupAIConsentManager(); setupAIConsentQuickStatus(); setupReferenciasTabs(); });
    } else {
        init();
        setupNavAvisoScroll();
        setupAIConsentManager();
        setupAIConsentQuickStatus();
        setupReferenciasTabs();
    }
})();