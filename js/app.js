/**
 * NossoDireito — app.js
 * Projeto sem fins lucrativos
 * Zero coleta de dados | 100% local | LGPD Art. 4º, I
 *
 * Security: AES-GCM-256 encryption at rest (Web Crypto API)
 * Storage: IndexedDB with encrypted file payloads
 * Privacy: Zero network transmission, zero cookies, zero tracking
 */

(function () {
    'use strict';

    // ========================
    // Security: Prototype Pollution Guard (CWE-1321)
    // ========================
    // Freeze Object.prototype to prevent __proto__ / constructor.prototype attacks
    // via JSON payloads, localStorage, or URL parameters.
    Object.freeze(Object.prototype);
    Object.freeze(Array.prototype);

    /**
     * Safe JSON parse — strips __proto__ and constructor keys (CWE-1321).
     * @param {string} str - JSON string to parse
     * @returns {*} Parsed value with prototype-polluting keys removed
     */
    function safeJsonParse(str) {
        return JSON.parse(str, (key, value) => {
            if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
                return undefined;
            }
            return value;
        });
    }

    /**
     * Deep freeze an object tree — prevent runtime mutation (CWE-471).
     * @param {Object} obj - Object to freeze recursively
     * @returns {Object} Frozen object
     */
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

    /**
     * Resilient fetch with retry — handles spotty connections in rural areas.
     * @param {string} url - URL to fetch
     * @param {number} retries - Max retry attempts (default 2)
     * @param {number} delay - Initial delay in ms (doubles each retry)
     * @returns {Promise<Response>}
     */
    async function resilientFetch(url, retries = 2, delay = 500) {
        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                const res = await fetch(url);
                if (res.ok) return res;
                if (res.status >= 400 && res.status < 500) throw new Error(`HTTP ${res.status}`); // Don't retry 4xx
            } catch (err) {
                if (attempt === retries) throw err;
                await new Promise(r => setTimeout(r, delay * Math.pow(2, attempt)));
            }
        }
    }

    // ========================
    // State
    // ========================
    let direitosData = null;
    let fontesData = null;
    let docsMestreData = null;
    let instituicoesData = null;
    let orgaosEstaduaisData = null;
    let classificacaoData = null;
    let jsonMeta = null;
    let UPPERCASE_ONLY_TERMS = new Set();
    let CID_RANGE_MAP = {};
    let KEYWORD_MAP = {};
    const STORAGE_PREFIX = 'nossodireito_';
    const DB_NAME = 'NossoDireitoDB';
    const DB_VERSION = 2; // v2: added crypto_keys store + encrypted file data
    const STORE_NAME = 'documentos';
    const CRYPTO_STORE = 'crypto_keys';
    const CRYPTO_KEY_ID = 'master_aes_key';
    const MAX_FILES = 5;
    const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
    const FILE_TTL_MINUTES = 15; // files auto-expire after 15 minutes (consulta pontual)
    const ALLOWED_TYPES = [
        'application/pdf',
        'image/jpeg',
        'image/png',
    ];
    const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
    const CRYPTO_AVAILABLE = typeof crypto !== 'undefined' && typeof crypto.subtle !== 'undefined';

    // ========================
    // Accessibility Toolbar
    // ========================
    const A11Y_FONT_KEY = STORAGE_PREFIX + 'font_size';
    const A11Y_CONTRAST_KEY = STORAGE_PREFIX + 'high_contrast';
    const FONT_STEPS = [14, 15, 16, 18, 20, 22]; // px
    const FONT_DEFAULT = 16;

    function setupAccessibilityToolbar() {
        const btnDecrease = document.getElementById('a11yFontDecrease');
        const btnReset = document.getElementById('a11yFontReset');
        const btnIncrease = document.getElementById('a11yFontIncrease');
        const btnContrast = document.getElementById('a11yContrast');
        const btnLibras = document.getElementById('a11yLibras');

        // --- Font size ---
        let currentSize = FONT_DEFAULT;
        try {
            const saved = localStorage.getItem(A11Y_FONT_KEY);
            if (saved && FONT_STEPS.includes(Number(saved))) currentSize = Number(saved);
        } catch (_) { /* private browsing */ }
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

        // --- High Contrast ---
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
            if (btnContrast) btnContrast.setAttribute('aria-pressed', String(on));
            try { localStorage.setItem(A11Y_CONTRAST_KEY, String(on)); } catch (_) { }
        }

        // --- VLibras init + toggle ---
        if (typeof window.VLibras !== 'undefined') { try { new window.VLibras.Widget('https://vlibras.gov.br/app'); } catch (_) { /* already init */ } }
        if (btnLibras) btnLibras.addEventListener('click', () => {
            const vwBtn = document.querySelector('[vw-access-button]');
            if (vwBtn) {
                vwBtn.click();
            } else {
                showToast('VLibras não carregou. Verifique sua conexão e recarregue a página.', 'warning');
            }
        });

        // --- Leitura em voz alta (Web Speech API — 100% nativo, sem dependência externa) ---
        const btnReadAloud = document.getElementById('a11yReadAloud');
        const TTS_AVAILABLE = typeof speechSynthesis !== 'undefined';
        let ttsActive = false;

        /**
         * Obtém o texto visível da seção atualmente mais próxima do viewport.
         * Prioriza seções com conteúdo real (ignora seções ocultas e vazias).
         */
        function getVisibleSectionText() {
            const sections = document.querySelectorAll('main section:not([style*="display:none"])');
            let bestSection = null;
            let bestDistance = Infinity;

            for (const section of sections) {
                if (section.hidden) continue;
                const rect = section.getBoundingClientRect();
                // Seção visível ou próxima do topo
                const distance = Math.abs(rect.top - 80); // 80px offset for navbar
                if (distance < bestDistance) {
                    bestDistance = distance;
                    bestSection = section;
                }
            }

            if (!bestSection) return '';

            // Extrair apenas texto útil (ignora scripts, styles, inputs)
            const clone = bestSection.cloneNode(true);
            clone.querySelectorAll('script, style, input, button, [aria-hidden="true"]').forEach(el => el.remove());
            const text = clone.textContent
                .replace(/\s+/g, ' ')
                .replace(/[📋🔍✅📎📄🔗🏥🏢🤝📜🏛️⚖️💚♿💡⚠️📲📥🗑️🔲🤟🔊⏳]/g, '') // Remove emojis
                .trim();

            return text;
        }

        /**
         * Encontra a melhor voz pt-BR disponível no dispositivo.
         * Prioriza vozes do Google e Microsoft por qualidade superior.
         */
        function getBestPtBrVoice() {
            const voices = speechSynthesis.getVoices();
            const ptVoices = voices.filter(v => v.lang.startsWith('pt'));
            if (ptVoices.length === 0) return null;

            // Prioridade: pt-BR > pt-PT, Google/Microsoft > outros
            const ranked = ptVoices.sort((a, b) => {
                const aScore = (a.lang === 'pt-BR' ? 10 : 0) + (a.name.includes('Google') ? 5 : 0) + (a.name.includes('Microsoft') ? 4 : 0);
                const bScore = (b.lang === 'pt-BR' ? 10 : 0) + (b.name.includes('Google') ? 5 : 0) + (b.name.includes('Microsoft') ? 4 : 0);
                return bScore - aScore;
            });
            return ranked[0];
        }

        function stopReading() {
            speechSynthesis.cancel();
            ttsActive = false;
            if (btnReadAloud) {
                btnReadAloud.textContent = '🔊 Ouvir';
                btnReadAloud.setAttribute('aria-pressed', 'false');
            }
        }

        function startReading() {
            const text = getVisibleSectionText();
            if (!text) {
                showToast('Não há conteúdo para ler nesta seção.', 'info');
                return;
            }

            // Limitar a ~2000 caracteres para não travar o navegador
            const truncated = text.length > 2000 ? text.substring(0, 2000) + '...' : text;

            const utterance = new SpeechSynthesisUtterance(truncated);
            utterance.lang = 'pt-BR';
            utterance.rate = 0.9;  // Velocidade levemente reduzida para clareza
            utterance.pitch = 1.0;

            const voice = getBestPtBrVoice();
            if (voice) utterance.voice = voice;

            speechSynthesis.cancel();
            speechSynthesis.speak(utterance);
            ttsActive = true;
            // Chrome 15s TTS bug workaround
            const ka = setInterval(() => { if (!ttsActive) { clearInterval(ka); return; } speechSynthesis.pause(); speechSynthesis.resume(); }, 10000);
            utterance.onend = () => { clearInterval(ka); stopReading(); };
            utterance.onerror = () => { clearInterval(ka); stopReading(); showToast('Erro na leitura. Seu navegador pode não suportar voz em português.', 'warning'); };

            if (btnReadAloud) {
                btnReadAloud.textContent = '⏹️ Parar';
                btnReadAloud.setAttribute('aria-pressed', 'true');
            }
        }

        if (btnReadAloud && TTS_AVAILABLE) {
            btnReadAloud.addEventListener('click', () => {
                if (ttsActive) {
                    stopReading();
                } else {
                    startReading();
                }
            });

            // Garantir que vozes estejam carregadas (Chrome carrega async)
            if (speechSynthesis.getVoices().length === 0) {
                speechSynthesis.addEventListener('voiceschanged', () => { }, { once: true });
            }
        } else if (btnReadAloud && !TTS_AVAILABLE) {
            // Navegador sem suporte a TTS — esconder botão
            btnReadAloud.style.display = 'none';
        }

        // Parar leitura ao navegar para outra seção
        window.addEventListener('hashchange', () => {
            if (ttsActive) stopReading();
        });
    }

    // Run toolbar setup immediately (before DOMContentLoaded, toolbar is in static HTML)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupAccessibilityToolbar);
    } else {
        setupAccessibilityToolbar();
    }

    // pdf.js worker — setup when available (may be lazy-loaded)
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

    // ========================
    // Toast Notifications (replaces alert())
    // ========================
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.setAttribute('role', 'alert');
        document.body.appendChild(toast);
        setTimeout(() => { if (toast.parentNode) toast.remove(); }, 5000);
    }

    // Accessible confirm dialog (replaces confirm())
    function confirmAction(msg, cb) {
        const d = document.createElement('dialog');
        d.className = 'confirm-dialog';
        d.setAttribute('role', 'alertdialog');
        d.setAttribute('aria-label', msg);
        d.innerHTML = '<p>' + msg + '</p><div class="confirm-actions"><button>Cancelar</button><button class="btn-confirm">Confirmar</button></div>';
        document.body.appendChild(d);
        d.showModal();
        d.onclick = e => { if (e.target.tagName === 'BUTTON') { const ok = e.target.classList.contains('btn-confirm'); d.close(); d.remove(); if (ok) cb(); } };
    }

    // ========================
    // DOM References
    // ========================
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const dom = {
        disclaimerModal: $('#disclaimerModal'),
        acceptBtn: $('#acceptDisclaimer'),
        menuToggle: $('#menuToggle'),
        navLinks: $('#navLinks'),
        searchInput: $('#searchInput'),
        searchBtn: $('#searchBtn'),
        searchResults: $('#searchResults'),
        categoryGrid: $('#categoryGrid'),
        detalheSection: $('#detalhe'),
        detalheContent: $('#detalheContent'),
        voltarBtn: $('#voltarBtn'),
        categoriasSection: $('#categorias'),
        lastUpdate: $('#lastUpdate'),
        showDisclaimer: $('#showDisclaimer'),
        // New sections
        uploadZone: $('#uploadZone'),
        fileInput: $('#fileInput'),
        fileList: $('#fileList'),
        deleteAllFiles: $('#deleteAllFiles'),
        docsChecklist: $('#docsChecklist'),
        // Analysis
        analysisResults: $('#analysisResults'),
        analysisLoading: $('#analysisLoading'),
        analysisContent: $('#analysisContent'),
        closeAnalysis: $('#closeAnalysis'),
        exportPdf: $('#exportPdf'),
        // Transparency
        fontesLegislacao: $('#fontesLegislacao'),
        fontesServicos: $('#fontesServicos'),
        fontesNormativas: $('#fontesNormativas'),
        // Institucions
        instituicoesGrid: $('#instituicoesGrid'),
        // Orgaos Estaduais
        orgaosEstaduaisGrid: $('#orgaosEstaduaisGrid'),
        // Classificacao CID
        classificacaoGrid: $('#classificacaoGrid'),
        // Meta
        transLastUpdate: $('#transLastUpdate'),
        transNextReview: $('#transNextReview'),
        transVersion: $('#transVersion'),
        // Footer version badge
        footerVersion: $('#footerVersion'),
        // Dynamic links
        linksGrid: $('#linksGrid'),
        // Staleness banner
        stalenessBanner: $('#stalenessBanner'),
        staleDays: $('#staleDays'),
        // Hero dynamic stats
        heroCatCount: $('#heroCatCount'),
        heroFontesCount: $('#heroFontesCount'),
    };

    // ========================
    // Init
    // ========================
    async function init() {
        setupDisclaimer();
        setupNavigation();
        setupSearch();
        setupChecklist();
        setupFooter();
        await loadData();
        enrichGovBr(); // fire-and-forget — non-blocking
        setupFooterVersion();
        renderCategories();
        renderTransparency();
        renderInstituicoes();
        renderOrgaosEstaduais();
        renderClassificacao();
        renderDocsChecklist();
        renderLinksUteis();
        renderHeroStats();
        checkStaleness();
        setupUpload();
        setupAnalysis();
        await cleanupExpiredFiles();
        await renderFileList();

        // Periodic cleanup — check every 60s for expired files
        setInterval(async () => {
            const removed = await cleanupExpiredFiles();
            if (removed > 0) await renderFileList();
        }, 60000);
    }

    // ========================
    // Disclaimer Modal
    // ========================
    function setupDisclaimer() {
        function closeModal() {
            dom.disclaimerModal.classList.add('hidden');
            dom.disclaimerModal.setAttribute('aria-hidden', 'true');
            if (dom.showDisclaimer) dom.showDisclaimer.focus();
        }

        function openModal() {
            dom.disclaimerModal.classList.remove('hidden');
            dom.disclaimerModal.setAttribute('aria-hidden', 'false');
            const firstFocusable = dom.disclaimerModal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) firstFocusable.focus();
        }

        // Focus trap inside modal
        dom.disclaimerModal.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const focusable = dom.disclaimerModal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
                if (focusable.length === 0) return;
                const first = focusable[0];
                const last = focusable[focusable.length - 1];
                if (e.shiftKey) {
                    if (document.activeElement === first) { e.preventDefault(); last.focus(); }
                } else {
                    if (document.activeElement === last) { e.preventDefault(); first.focus(); }
                }
            }
            if (e.key === 'Escape') closeModal();
        });

        // Close on backdrop click
        dom.disclaimerModal.addEventListener('click', (e) => {
            if (e.target === dom.disclaimerModal) closeModal();
        });

        dom.acceptBtn.addEventListener('click', closeModal);

        dom.showDisclaimer.addEventListener('click', (e) => {
            e.preventDefault();
            openModal();
        });
    }

    // ========================
    // Navigation
    // ========================
    function setupNavigation() {
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
            link.addEventListener('click', () => {
                dom.navLinks.classList.remove('open');
                dom.menuToggle.classList.remove('open');
                dom.menuToggle.setAttribute('aria-expanded', 'false');
                dom.menuToggle.setAttribute('aria-label', 'Abrir menu');
            });
        });

        const sections = $$('section[id]');
        const navAnchors = dom.navLinks.querySelectorAll('a');

        // IntersectionObserver guard — Safari 12.0 doesn't support it
        if (!('IntersectionObserver' in window)) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const id = entry.target.id;
                        navAnchors.forEach((a) => {
                            a.classList.toggle(
                                'active',
                                a.getAttribute('href') === `#${id}`
                            );
                        });
                    }
                });
            },
            { rootMargin: '-100px 0px -60% 0px' }
        );

        sections.forEach((s) => observer.observe(s));

        dom.voltarBtn.addEventListener('click', () => {
            dom.detalheSection.style.display = 'none';
            dom.categoriasSection.style.display = '';
            history.pushState({ view: 'categorias' }, '', '#categorias');
            dom.categoriasSection.scrollIntoView({ behavior: 'smooth' });
            const h2 = dom.categoriasSection.querySelector('h2');
            if (h2) { h2.setAttribute('tabindex', '-1'); h2.focus({ preventScroll: true }); }
        });

        // Browser back/forward button support for detail view
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.view === 'detalhe' && e.state.id) {
                showDetalhe(e.state.id, true);
            } else {
                dom.detalheSection.style.display = 'none';
                dom.categoriasSection.style.display = '';
            }
        });
    }

    // ========================
    // Data Loading
    // ========================
    async function loadData() {
        try {
            const res = await resilientFetch('data/direitos.json');
            const json = await res.json();

            // Deep-freeze all data arrays — prevent runtime mutation (CWE-471)
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
            dom.categoryGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align:center; padding:32px; color:var(--text-muted);">
                    <p>⚠️ Não foi possível carregar os dados.</p>
                    <p style="font-size:0.9rem;">Verifique se o arquivo <code>data/direitos.json</code> está acessível.</p>
                </div>`;
        }

        // Load matching engine separately — graceful degradation.
        // If this fails, manual search/browse still works; only PDF analysis is impaired.
        try {
            const meRes = await resilientFetch('data/matching_engine.json');
            const me = await meRes.json();
            UPPERCASE_ONLY_TERMS = Object.freeze(new Set(me.uppercase_only_terms));
            CID_RANGE_MAP = deepFreeze(me.cid_range_map);
            KEYWORD_MAP = deepFreeze(me.keyword_map);
        } catch (err) {
            console.warn('Motor de correspondência não carregou — análise de documentos pode ser limitada:', err.message);
        }
    }

    // Gov.br API enrichment — tries to confirm digital service availability.
    // Graceful degradation: if CORS blocks or API is down, badge still shows static info.
    async function enrichGovBr() {
        try {
            const r = await fetch('https://servicos.gov.br/api/v1/servicos/10783',
                { signal: AbortSignal.timeout(4000) });
            if (r.ok) sessionStorage.setItem('govbr_10783', '1');
        } catch { /* gov.br API sem CORS — silencioso */ }
    }

    // ========================
    // Render Categories
    // ========================
    function renderCategories() {
        if (!direitosData) return;

        dom.categoryGrid.innerHTML = direitosData
            .map(
                (cat) => `
            <div class="category-card" tabindex="0" role="button"
                 aria-label="Ver detalhes sobre ${escapeHtml(cat.titulo)}"
                 data-id="${cat.id}">
                <span class="category-icon">${cat.icone}</span>
                <h3>${escapeHtml(cat.titulo)}</h3>
                <p>${escapeHtml(cat.resumo)}</p>
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
    }

    // ========================
    // Detail View
    // ========================
    function showDetalhe(id, skipHistory) {
        const cat = direitosData.find((c) => c.id === id);
        if (!cat) return;

        dom.categoriasSection.style.display = 'none';
        dom.detalheSection.style.display = '';

        // Push browser history so back button returns to categories
        if (!skipHistory) {
            history.pushState({ view: 'detalhe', id }, '', `#direito/${id}`);
        }

        let html = `
            <h2>${cat.icone} ${escapeHtml(cat.titulo)}</h2>
            <p class="detalhe-resumo">${escapeHtml(cat.resumo)}</p>`;

        // Valor
        if (cat.valor) {
            html += `<div class="detalhe-section">
                <h3>💰 Valor</h3>
                <span class="valor-destaque">${escapeHtml(cat.valor)}</span>
            </div>`;
        }

        // Base legal
        if (cat.base_legal && cat.base_legal.length) {
            html += `<div class="detalhe-section">
                <h3>📜 Base Legal</h3>
                <div>${cat.base_legal
                    .map(
                        (l) =>
                            `<a class="legal-link" href="${escapeHtml(l.link)}" target="_blank" rel="noopener noreferrer">
                            📄 ${escapeHtml(l.lei)}${l.artigo ? ' — ' + escapeHtml(l.artigo) : ''}
                        </a>`
                    )
                    .join('')}</div>
            </div>`;
        }

        // Requisitos
        if (cat.requisitos && cat.requisitos.length) {
            html += `<div class="detalhe-section">
                <h3>📋 Requisitos</h3>
                <ul>${cat.requisitos.map((r) => `<li>${escapeHtml(r)}</li>`).join('')}</ul>
            </div>`;
        }

        // Documentos
        if (cat.documentos && cat.documentos.length) {
            html += `<div class="detalhe-section">
                <h3>📄 Documentos Necessários</h3>
                <ul>${cat.documentos.map((d) => `<li>${escapeHtml(d)}</li>`).join('')}</ul>
            </div>`;
        }

        // Passo a passo
        if (cat.passo_a_passo && cat.passo_a_passo.length) {
            html += `<div class="detalhe-section">
                <h3>👣 Passo a Passo</h3>
                <ol>${cat.passo_a_passo.map((p) => `<li>${escapeHtml(p)}</li>`).join('')}</ol>
            </div>`;
        }

        // Onde
        if (cat.onde) {
            html += `<div class="detalhe-section">
                <h3>📍 Onde Solicitar</h3>
                <p>${escapeHtml(cat.onde)}</p>
            </div>`;
        }

        // Dicas
        if (cat.dicas && cat.dicas.length) {
            html += `<div class="detalhe-section">
                <h3>💡 Dicas Importantes</h3>
                ${cat.dicas.map((d) => `<div class="dica-item">${escapeHtml(d)}</div>`).join('')}
            </div>`;
        }

        // IPVA por Estado (tabela colapsável)
        if (cat.ipva_estados && cat.ipva_estados.length) {
            html += `<div class="detalhe-section"><h3>🚗 Isenção de IPVA por Estado</h3>
                <details><summary>Ver legislação dos ${cat.ipva_estados.length} estados</summary>
                <div class="table-wrapper"><table class="ipva-table">
                <thead><tr><th>UF</th><th>Lei</th><th>Art.</th><th>SEFAZ</th></tr></thead>
                <tbody>${cat.ipva_estados.map(e => `<tr><td>${escapeHtml(e.uf)}</td><td>${escapeHtml(e.lei)}</td><td>${escapeHtml(e.art)}</td><td><a href="${escapeHtml(e.sefaz)}" target="_blank" rel="noopener noreferrer">Consultar</a></td></tr>`).join('')}</tbody>
                </table></div></details></div>`;
        }

        // Links
        if (cat.links && cat.links.length) {
            html += `<div class="detalhe-section">
                <h3>🔗 Links Úteis</h3>
                <div>${cat.links
                    .filter((l) => isSafeUrl(l.url))
                    .map(
                        (l) =>
                            `<a class="legal-link" href="${escapeHtml(l.url)}" target="_blank" rel="noopener noreferrer">
                            🌐 ${escapeHtml(l.titulo)}
                        </a>`
                    )
                    .join('')}</div>
            </div>`;
        }

        // Gov.br service badge
        if (cat.govbr_servico_id) {
            const live = sessionStorage.getItem('govbr_' + cat.govbr_servico_id);
            html += `<div class="detalhe-section" style="text-align:center">
                <a href="https://www.gov.br/pt-br/servicos/obter-isencao-de-impostos-para-comprar-carro" target="_blank" rel="noopener noreferrer" class="tag" style="display:inline-block;background:${live ? '#168821' : '#1351b4'};color:#fff;text-decoration:none;padding:6px 16px;border-radius:20px;font-size:0.95rem">
                🇧🇷 ${live ? 'Serviço digital confirmado no gov.br' : 'Acessar serviço no gov.br'}
                </a></div>`;
        }

        // Tags
        if (cat.tags && cat.tags.length) {
            html += `<div class="detalhe-tags">
                ${cat.tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
            </div>`;
        }

        // WhatsApp share button
        const shareText = encodeURIComponent(
            `${cat.icone} ${cat.titulo}\n${cat.resumo}\n\nVeja mais em: https://nossodireito.fabiotreze.com`
        );
        html += `<div class="detalhe-section" style="text-align:center;padding-top:8px;">
            <a href="https://wa.me/?text=${shareText}" target="_blank" rel="noopener noreferrer"
               class="btn btn-whatsapp" aria-label="Compartilhar no WhatsApp">
               📲 Compartilhar no WhatsApp
            </a>
        </div>`;

        dom.detalheContent.innerHTML = html;
        dom.detalheSection.scrollIntoView({ behavior: 'smooth' });
        const h2 = dom.detalheSection.querySelector('h2');
        if (h2) { h2.setAttribute('tabindex', '-1'); h2.focus({ preventScroll: true }); }
    }

    // ========================
    // Search
    // ========================
    function setupSearch() {
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
            if (e.key === 'Enter') doSearch();
        });

        let timer;
        dom.searchInput.addEventListener('input', () => {
            clearTimeout(timer);
            timer = setTimeout(doSearch, 300);
        });
    }

    function performSearch(query) {
        const terms = query
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .split(/\s+/)
            .filter(Boolean);

        const scored = direitosData
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

                const score = terms.reduce((acc, term) => {
                    const count = (searchable.match(new RegExp(escapeRegex(term), 'g')) || []).length;
                    return acc + count;
                }, 0);

                return { cat, score };
            })
            .filter((r) => r.score > 0)
            .sort((a, b) => b.score - a.score);

        if (scored.length === 0) {
            dom.searchResults.innerHTML = `
                <div class="search-no-results">
                    <p>Nenhum resultado para "<strong>${escapeHtml(query)}</strong>".</p>
                    <p>Tente palavras como: BPC, escola, plano de saúde, transporte, TEA...</p>
                </div>`;
            return;
        }

        dom.searchResults.innerHTML = scored
            .map(
                ({ cat }) => `
            <div class="search-result-item" data-id="${cat.id}" tabindex="0" role="button">
                <span class="search-result-icon">${cat.icone}</span>
                <div class="search-result-info">
                    <h4>${escapeHtml(cat.titulo)}</h4>
                    <p>${escapeHtml(cat.resumo)}</p>
                </div>
            </div>`
            )
            .join('');

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

    // ========================
    // Checklist (Local Storage)
    // ========================
    function setupChecklist() {
        const checkboxes = $$('.checklist-item input[type="checkbox"]');
        const saved = localGet('checklist') || {};
        const total = checkboxes.length;
        const progressText = $('#checklistProgress');
        const progressBar = $('#checklistProgressBar');

        function updateProgress() {
            const done = $$('.checklist-item input[type="checkbox"]:checked').length;
            if (progressText) progressText.textContent = `${done} de ${total} concluídos`;
            if (progressBar) {
                progressBar.style.width = `${Math.round(done / total * 100)}%`;
                progressBar.closest('.progress-bar')?.setAttribute('aria-valuenow', done);
            }
        }

        checkboxes.forEach((cb) => {
            const step = cb.dataset.step;
            if (saved[step]) cb.checked = true;

            cb.addEventListener('change', () => {
                const state = localGet('checklist') || {};
                if (cb.checked) {
                    state[step] = true;
                } else {
                    delete state[step];
                }
                localSet('checklist', state);
                updateProgress();
            });
        });

        updateProgress();
    }

    // ========================
    // Transparency Section
    // ========================
    function renderTransparency() {
        if (!fontesData || !jsonMeta) return;

        // Meta
        if (dom.transLastUpdate) {
            dom.transLastUpdate.textContent = formatDate(jsonMeta.ultima_atualizacao);
        }
        if (dom.transNextReview) {
            dom.transNextReview.textContent = formatDate(jsonMeta.proxima_revisao);
        }
        if (dom.transVersion) {
            dom.transVersion.textContent = `v${jsonMeta.versao}`;
        }

        // Split by type
        const legislacao = fontesData.filter((f) => f.tipo === 'legislacao');
        const servicos = fontesData.filter((f) => f.tipo === 'servico');
        const normativas = fontesData.filter((f) => f.tipo === 'normativa');

        const renderFonte = (f) => {
            const tipoIcon = f.tipo === 'legislacao' ? '📜' : f.tipo === 'servico' ? '🌐' : '📋';
            const artigos = f.artigos_referenciados
                ? `<div class="fonte-artigos">Artigos: ${f.artigos_referenciados.join(', ')}</div>`
                : '';
            return `
                <div class="fonte-item">
                    <span class="fonte-icon">${tipoIcon}</span>
                    <div class="fonte-info">
                        <div class="fonte-nome">${escapeHtml(f.nome)}</div>
                        <div class="fonte-orgao">${escapeHtml(f.orgao)}</div>
                        ${artigos}
                    </div>
                    <div class="fonte-data">Consultado<br>${formatDate(f.consultado_em)}</div>
                    <div class="fonte-link">
                        ${isSafeUrl(f.url) ? `<a href="${escapeHtml(f.url)}" target="_blank" rel="noopener noreferrer">Abrir ↗</a>` : ''}
                    </div>
                </div>`;
        };

        if (dom.fontesLegislacao) {
            dom.fontesLegislacao.innerHTML = legislacao.map(renderFonte).join('');
        }
        if (dom.fontesServicos) {
            dom.fontesServicos.innerHTML = servicos.map(renderFonte).join('');
        }
        if (dom.fontesNormativas) {
            dom.fontesNormativas.innerHTML = normativas.length
                ? normativas.map(renderFonte).join('')
                : '<p style="color:var(--text-light);font-size:0.9rem;">Nenhuma normativa adicional no momento.</p>';
        }
    }

    // ========================
    // Documents Checklist (Master)
    // ========================
    function renderDocsChecklist() {
        if (!docsMestreData || !direitosData) return;

        const saved = localGet('docs_checklist') || {};

        // Build category name map
        const catNameMap = {};
        direitosData.forEach((c) => {
            catNameMap[c.id] = c.titulo.split('—')[0].trim();
        });

        dom.docsChecklist.innerHTML = docsMestreData
            .map((doc) => {
                const checked = saved[doc.id] ? 'checked' : '';
                const catTags = (doc.categorias || [])
                    .map((cid) => `<span class="doc-cat-tag">${escapeHtml(catNameMap[cid] || cid)}</span>`)
                    .join('');

                return `
                <div class="doc-master-item">
                    <label class="doc-master-header">
                        <input type="checkbox" data-doc-id="${doc.id}" ${checked}>
                        <div class="doc-master-info">
                            <div class="doc-master-name">${escapeHtml(doc.nome)}</div>
                            <div class="doc-master-desc">${escapeHtml(doc.descricao)}</div>
                            <div class="doc-master-categories">${catTags}</div>
                        </div>
                    </label>
                    ${doc.dica ? `<div class="doc-master-dica">💡 ${escapeHtml(doc.dica)}</div>` : ''}
                </div>`;
            })
            .join('');

        // Bind events
        dom.docsChecklist.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
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

    // ========================
    // Instituições de Apoio
    // ========================
    function renderInstituicoes() {
        if (!instituicoesData || !direitosData) return;

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
                    const tipoIcon = inst.tipo === 'governamental' ? '🏛️' : inst.tipo === 'ong' ? '💚' : '⚖️';
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
                            <span class="inst-tipo-badge ${inst.tipo}">${tipoIcon} ${tipoLabel}</span>
                        </div>
                        <h4 class="inst-nome">${escapeHtml(inst.nome)}</h4>
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

        // Filter buttons
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

    // ========================
    // Dynamic Links Úteis
    // ========================
    function renderLinksUteis() {
        if (!fontesData || !direitosData || !dom.linksGrid) return;

        // Collect unique service links from fontes
        const seen = new Set();
        const links = [];

        // 1. Service-type fontes (portals)
        fontesData
            .filter((f) => f.tipo === 'servico')
            .forEach((f) => {
                if (!seen.has(f.url)) {
                    seen.add(f.url);
                    links.push({ titulo: f.nome, url: f.url, orgao: f.orgao });
                }
            });

        // 2. Per-category utility links
        direitosData.forEach((cat) => {
            (cat.links || []).forEach((lk) => {
                if (!seen.has(lk.url)) {
                    seen.add(lk.url);
                    links.push({ titulo: lk.titulo, url: lk.url, orgao: '' });
                }
            });
        });

        dom.linksGrid.innerHTML = links
            .filter((lk) => isSafeUrl(lk.url))
            .map((lk) => {
                const isTel = lk.url.trim().toLowerCase().startsWith('tel:');
                const domain = (() => {
                    if (isTel) return lk.url.replace('tel:', '');
                    try { return new URL(lk.url).hostname.replace('www.', ''); }
                    catch { return ''; }
                })();
                const icon = isTel ? '📞'
                    : domain.includes('cfm.org') ? '👨‍⚕️'
                        : domain.includes('cfp.org') ? '🧠'
                            : domain.includes('who.int') ? '🌐'
                                : domain.includes('gov.br') ? '🏛️'
                                    : domain.includes('inss') ? '📋'
                                        : domain.includes('mds.gov') ? '🏠'
                                            : '🔗';
                return `
                <a href="${escapeHtml(lk.url)}" class="link-card" target="_blank" rel="noopener noreferrer">
                    <span class="link-icon">${icon}</span>
                    <span class="link-title">${escapeHtml(lk.titulo)}</span>
                    <span class="link-domain">${escapeHtml(domain)}</span>
                </a>`;
            })
            .join('');
    }

    // ========================
    // Hero Stats (dynamic)
    // ========================
    function renderHeroStats() {
        if (!direitosData || !fontesData) return;
        if (dom.heroCatCount) {
            dom.heroCatCount.textContent = `${direitosData.length}`;
        }
        if (dom.heroFontesCount) {
            dom.heroFontesCount.textContent = `${fontesData.length}`;
        }
    }

    // ========================
    // Órgãos Estaduais
    // ========================
    function renderOrgaosEstaduais() {
        if (!orgaosEstaduaisData || !dom.orgaosEstaduaisGrid) return;

        // Agrupamento por região
        const regioes = {
            'Norte': ['AC', 'AM', 'AP', 'PA', 'RO', 'RR', 'TO'],
            'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
            'Centro-Oeste': ['DF', 'GO', 'MS', 'MT'],
            'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
            'Sul': ['PR', 'RS', 'SC'],
        };

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
                    return `
                    <div class="orgao-card">
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

        // Filter buttons
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

    // ========================
    // Classificação de Deficiência (CID-10 / CID-11)
    // ========================
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
                            <td class="classif-tipo"><strong>${escapeHtml(c.tipo)}</strong></td>
                            <td class="classif-cid"><code>${escapeHtml(c.cid10)}</code></td>
                            <td class="classif-cid"><code>${escapeHtml(c.cid11)}</code></td>
                            <td class="classif-criterio">${escapeHtml(c.criterio)}</td>
                        </tr>`).join('')}
                    </tbody>
                </table>
            </div>
            <p class="classif-note">
                💡 <strong>Dica:</strong> A CID-11 (OMS 2022) está sendo adotada gradualmente.
                No Brasil, a maioria dos laudos ainda usa CID-10. O sistema aceita ambas as codificações.
            </p>`;
    }

    // ========================
    // Staleness Banner
    // ========================
    function checkStaleness() {
        if (!jsonMeta || !dom.stalenessBanner) return;

        const updated = new Date(jsonMeta.ultima_atualizacao);
        const now = new Date();
        const diffDays = Math.floor((now - updated) / (1000 * 60 * 60 * 24));
        const STALE_THRESHOLD = 30; // days

        if (diffDays > STALE_THRESHOLD) {
            if (dom.staleDays) {
                dom.staleDays.textContent = `há ${diffDays} dias`;
            }
            dom.stalenessBanner.hidden = false;
        } else {
            dom.stalenessBanner.hidden = true;
        }
    }

    // ========================
    // File Upload (IndexedDB)
    // ========================

    /**
     * Revela a área de upload de documentos (hidden by default).
     * Chamado pelo botão hero "Meus Documentos" e pelo nav link.
     */
    function revealDocsUpload() {
        const area = document.getElementById('docsUploadArea');
        if (area) area.style.display = '';
    }

    // Wire hero button + nav link to reveal docs upload on click
    (function setupDocsReveal() {
        const heroBtn = document.getElementById('heroDocsBtn');
        if (heroBtn) {
            heroBtn.addEventListener('click', revealDocsUpload);
        }
        // Also reveal when navigating via nav menu
        document.querySelectorAll('a[href="#documentos"]').forEach(link => {
            link.addEventListener('click', revealDocsUpload);
        });
    })();

    function setupUpload() {
        // Click to upload
        dom.uploadZone.addEventListener('click', () => dom.fileInput.click());
        dom.uploadZone.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                dom.fileInput.click();
            }
        });

        // File input change
        dom.fileInput.addEventListener('change', async (e) => {
            await handleFiles(e.target.files);
            e.target.value = ''; // reset
        });

        // Drag & drop
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
        });

        // Delete all
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
            // Validate type
            if (!ALLOWED_TYPES.includes(file.type)) {
                const parts = file.name.split('.');
                const ext = parts.length > 1 ? parts.pop().toLowerCase() : '';
                if (!ALLOWED_EXTENSIONS.includes('.' + ext)) {
                    showToast(`Formato não aceito: ${file.name}. Use PDF, JPG ou PNG.`, 'error');
                    continue;
                }
            }

            // Validate size
            if (file.size > MAX_FILE_SIZE) {
                showToast(`Arquivo muito grande: ${file.name} (${formatBytes(file.size)}). Máx: 5MB.`, 'error');
                continue;
            }

            // Read, encrypt, and store
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

            if (files.length === 0) {
                dom.fileList.innerHTML = '';
                dom.deleteAllFiles.style.display = 'none';
                return;
            }

            dom.deleteAllFiles.style.display = '';

            dom.fileList.innerHTML = files
                .map((f) => {
                    const icon = f.type === 'application/pdf' ? '📄' : '🖼️';
                    const date = new Date(f.addedAt).toLocaleDateString('pt-BR');
                    const cryptoBadge = f.encrypted ? '<span class="crypto-badge" title="Criptografia AES-256-GCM">🔐</span>' : '';
                    const expiresStr = f.expiresAt
                        ? `· ⏱️ ${formatTimeRemaining(f.expiresAt)}`
                        : '';
                    return `
                    <div class="file-item" data-file-id="${f.id}">
                        <label class="file-item-checkbox" title="Selecionar para análise">
                            <input type="checkbox" class="file-select-cb" data-id="${f.id}" checked>
                        </label>
                        <span class="file-item-icon">${icon}</span>
                        <div class="file-item-info">
                            <div class="file-item-name" title="${escapeHtml(f.name)}">${cryptoBadge}${escapeHtml(f.name)}</div>
                            <div class="file-item-meta">${formatBytes(f.size)} · Adicionado em ${date} ${expiresStr}</div>
                        </div>
                        <div class="file-item-actions">
                            <button class="btn-view" title="Visualizar" data-id="${f.id}">👁️ Ver</button>
                            <button class="btn-delete" title="Excluir" data-id="${f.id}">🗑️</button>
                        </div>
                    </div>`;
                })
                .join('');

            // Update global analyze button state
            updateAnalyzeButton();

            // Bind checkbox changes to update button
            dom.fileList.querySelectorAll('.file-select-cb').forEach((cb) => {
                cb.addEventListener('change', updateAnalyzeButton);
            });

            dom.fileList.querySelectorAll('.btn-view').forEach((btn) => {
                btn.addEventListener('click', async () => {
                    const file = await getFile(btn.dataset.id);
                    if (file) {
                        const plainData = await decryptFileData(file);
                        const blob = new Blob([plainData], { type: file.type });
                        const url = URL.createObjectURL(blob);
                        // Use <a> click instead of window.open — iOS Safari blocks popups from async callbacks
                        const a = document.createElement('a');
                        a.href = url;
                        a.target = '_blank';
                        a.rel = 'noopener';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        // Revoke blob URL quickly to limit exposure window
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

    // ========================
    // Document Analysis Engine
    // ========================

    /**
     * Atualiza o estado do botão global "Analisar Selecionados".
     */
    function updateAnalyzeButton() {
        const btn = document.getElementById('analyzeSelected');
        if (!btn) return;
        const checked = dom.fileList.querySelectorAll('.file-select-cb:checked');
        const count = checked.length;
        btn.disabled = count === 0;
        btn.textContent = count === 0
            ? '🔍 Enviar para análise local'
            : count === 1
                ? '🔍 Analisar 1 arquivo'
                : `🔍 Analisar ${count} arquivos`;
    }

    function setupAnalysis() {
        dom.closeAnalysis.addEventListener('click', () => {
            dom.analysisResults.style.display = 'none';
        });

        dom.exportPdf.addEventListener('click', () => {
            // Set date for print footer
            dom.analysisResults.setAttribute('data-print-date', new Date().toLocaleDateString('pt-BR'));
            // Temporarily mark body for print-only analysis view
            document.body.classList.add('printing-analysis');
            window.print();
            // Remove class after print dialog closes
            const cleanup = () => {
                document.body.classList.remove('printing-analysis');
                window.removeEventListener('afterprint', cleanup);
            };
            window.addEventListener('afterprint', cleanup);
            // Fallback: remove after 5s in case afterprint doesn't fire (iOS)
            setTimeout(cleanup, 5000);
        });

        // Global analyze button
        const analyzeBtn = document.getElementById('analyzeSelected');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', analyzeSelectedDocuments);
        }
    }

    /**
     * Analisa todos os documentos selecionados (checkbox) de forma unificada.
     * Concatena o texto extraído de todos os arquivos e faz matching único.
     * Exibe resultado consolidado mostrando de qual arquivo veio cada termo.
     * 100% local — nada é enviado para servidores.
     */
    async function analyzeSelectedDocuments() {
        const analyzeBtn = document.getElementById('analyzeSelected');
        const checkboxes = dom.fileList.querySelectorAll('.file-select-cb:checked');
        const fileIds = Array.from(checkboxes).map((cb) => cb.dataset.id);

        if (fileIds.length === 0) {
            showToast('Selecione pelo menos um arquivo para analisar.', 'warning');
            return;
        }

        // Desabilitar botão durante análise (evita duplo-clique)
        if (analyzeBtn) {
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = '⏳ Analisando...';
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
            // Carregar TODOS os arquivos do IndexedDB antes de processar
            // (evita problemas de conexão DB entre iterações)
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

            // Processar cada arquivo (extração de texto)
            for (let i = 0; i < filesToProcess.length; i++) {
                const { fileId, file } = filesToProcess[i];
                // Atualizar progresso no loading
                if (filesToProcess.length > 1) {
                    const loadingText = dom.analysisLoading.querySelector('p');
                    if (loadingText) {
                        loadingText.textContent = `Analisando ${i + 1} de ${filesToProcess.length}: ${file.name}`;
                    }
                }
                try {
                    const plainData = await decryptFileData(file);
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
                        <p>⚠️ Não foi possível analisar nenhum dos arquivos selecionados.</p>
                        ${errors.map((e) => `<p style=\"font-size:0.85rem;color:var(--text-muted);\">· ${escapeHtml(e.name)}: ${escapeHtml(e.reason)}</p>`).join('')}
                        <p style="font-size:0.85rem;margin-top:8px;">
                            💡 <strong>Dica:</strong> Navegue pelas <a href=\"#categorias\">categorias</a>
                            para encontrar seus direitos manualmente.
                        </p>
                    </div>`;
                return;
            }

            // Filtro: só analisar se houver termos médicos/saúde
            // Inclui variantes sem acento para PDFs que perdem acentuação na extração
            const medicalTerms = [
                'laudo', 'atestado', 'receita médica', 'receita medica', 'diagnóstico', 'diagnostico',
                'cid', 'crm', 'médico', 'medico', 'exame', 'prescrição', 'prescricao',
                'relatório médico', 'relatorio medico', 'doença', 'doenca', 'deficiência', 'deficiencia',
                'autismo', 'tea', 'psiquiatra', 'neurologista', 'fisioterapeuta', 'terapeuta',
                'psicólogo', 'psicologo', 'fonoaudiólogo', 'fonoaudiologo', 'terapia ocupacional',
                'transtorno', 'síndrome', 'sindrome', 'especialista', 'consulta médica', 'consulta medica',
                'encaminhamento', 'habilitação', 'habilitacao', 'reabilitação', 'reabilitacao',
                'paciente', 'prontuário', 'prontuario', 'anamnese', 'prognóstico', 'prognostico',
                'comorbidade', 'terapêutico', 'terapeutico', 'clínico', 'clinico', 'neuropediatra'
            ];
            // Texto original (preserva maiúsculas para matchRights)
            const originalText = allText.join('\n');
            // Texto lowercase para filtro médico
            const combinedTextLower = originalText.toLowerCase();
            const foundMedical = medicalTerms.some(term => combinedTextLower.includes(term));
            if (!foundMedical) {
                dom.analysisContent.innerHTML = `
                    <div class="analysis-error">
                        <p>⚠️ O documento enviado não parece ser um laudo, atestado ou documento médico.</p>
                        <p>Por favor, envie um documento relacionado à saúde (laudo, atestado, receita, diagnóstico, etc.) para análise dos direitos.</p>
                        <p style="font-size:0.85rem;margin-top:8px;">
                            💡 <strong>Dica:</strong> Navegue pelas <a href=\"#categorias\">categorias</a> para encontrar seus direitos manualmente.
                        </p>
                    </div>`;
                // Auto-delete arquivos analisados
                for (const id of successIds) {
                    try { await deleteFile(id); } catch (delErr) { console.warn('Erro ao descartar arquivo após análise:', delErr); }
                }
                await renderFileList();
                if (analyzeBtn) updateAnalyzeButton();
                dom.analysisLoading.style.display = 'none';
                return;
            }

            // Concatenate all text and file names for unified matching
            // IMPORTANTE: passar texto ORIGINAL (com maiúsculas) para matchRights,
            // pois a detecção de CID (F84, G80, 6A02) e siglas (TEA, BPC, SUS)
            // depende de case-sensitive matching no rawText.
            const combinedNames = fileNames.join(' ');
            const results = matchRights(originalText, combinedNames);
            const anyPdf = hasPdf.some(Boolean);

            renderAnalysisResults(results, fileNames, anyPdf, errors);

            // Auto-delete successfully analyzed files (consulta pontual)
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
                    <p>⚠️ Ocorreu um erro durante a análise.</p>
                    <p style="font-size:0.85rem;margin-top:8px;">
                        💡 <strong>Dica:</strong> Navegue pelas <a href=\"#categorias\">categorias</a>
                        para encontrar seus direitos manualmente.
                    </p>
                </div>`;
        } finally {
            dom.analysisLoading.style.display = 'none';
            // Restaurar loading text original
            const loadingText = dom.analysisLoading.querySelector('p');
            if (loadingText) {
                loadingText.textContent = 'Analisando documentos... (100% local, nada é enviado)';
            }
            // Reabilitar botão
            if (analyzeBtn) {
                updateAnalyzeButton();
            }
        }
    }

    /**
     * Extrai texto de um ArrayBuffer contendo um PDF usando pdf.js
     */
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

    /**
     * UPPERCASE_ONLY_TERMS, CID_RANGE_MAP and KEYWORD_MAP are now loaded
     * from data/matching_engine.json in loadData() — see state variables above.
     */

    /**
     * Regex para detectar qualquer código CID-10 (ex: F84, G80.1, Q90.0)
     * ou CID-11 (ex: 6A02, 6A02.0) que não esteja explicitamente no KEYWORD_MAP.
     * Captura apenas em MAIÚSCULAS no texto original.
     * Retornam regex NOVO a cada chamada para evitar problemas de lastIndex compartilhado.
     */
    function cidGenericRegex() { return /\b([A-Z]\d{2}(?:\.\d{1,2})?)\b/g; }
    function cid11GenericRegex() { return /\b(\d[A-Z]\d{2}(?:\.\d{1,2})?)\b/g; }
    function cid11TwoLetterRegex() { return /\b([A-Z]{2}\d{2}(?:\.\d{1,2})?)\b/g; }

    /**
     * Regex para detectar número de CRM em laudos médicos.
     * Formatos: CRM/SP 123456, CRM-12345/SP, CRM 12345 SP, CRM-SP 12345
     */
    function crmRegex() { return /\bCRM[\s/\-]*([A-Z]{2})?[\s/\-]*(\d{4,7})[\s/\-]*([A-Z]{2})?\b/gi; }

    /**
     * Faz matching do texto extraído contra as categorias do JSON.
     * Combina: (0) CID genérico, (1) KEYWORD_MAP, (2) category tags, (3) requisitos.
     *
     * Matching inteligente:
     * - Siglas curtas (ABA, TEA, CID, SUS…) só casam em MAIÚSCULAS no texto original,
     *   evitando falsos positivos com palavras comuns em português.
     * - Códigos CID-10/CID-11 são reconhecidos genericamente mesmo fora do KEYWORD_MAP.
     * - Termos longos e frases usam word-boundary case-insensitive (normalizado).
     *
     * @param {string} text — texto extraído dos PDFs
     * @param {string} fileName — nome(s) do(s) arquivo(s)
     * @returns {Array} resultados ordenados por score
     */
    function matchRights(text, fileName) {
        if (!direitosData) return [];

        const rawText = text + ' ' + fileName;           // preserva maiúsculas/minúsculas
        const normalizedText = normalizeText(rawText);    // minúsculo sem acentos
        const scores = {};

        // Initialize scores
        direitosData.forEach((cat) => {
            scores[cat.id] = { score: 0, matches: new Set() };
        });

        // ── Pass 0: Reconhecimento genérico de códigos CID ──
        // Captura QUALQUER código CID-10 (F84, G80.1…) ou CID-11 (6A02…)
        // que não esteja explicitamente no KEYWORD_MAP.
        // Regex criado fresh a cada chamada para evitar lastIndex compartilhado.
        const cidMatched = new Set();
        for (const cidRegex of [cidGenericRegex(), cid11GenericRegex(), cid11TwoLetterRegex()]) {
            let m;
            while ((m = cidRegex.exec(rawText)) !== null) {
                const code = m[1];
                const prefix = code.substring(0, 3).toLowerCase();
                // Se já coberto pelo KEYWORD_MAP, pular (Pass 1 cuida)
                if (KEYWORD_MAP[prefix] || KEYWORD_MAP[code.toLowerCase()]) continue;
                if (cidMatched.has(code)) continue;
                cidMatched.add(code);

                // Mapear pela letra inicial do CID
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

        // ── Pass 0b: Detecção de CRM (Conselho Regional de Medicina) ──
        // Detecta números CRM em laudos médicos, indicando documento médico válido.
        const crmMatch = crmRegex().exec(rawText);
        if (crmMatch) {
            const uf = crmMatch[1] || crmMatch[3] || '';
            const num = crmMatch[2];
            const crmLabel = uf ? `CRM/${uf} ${num}` : `CRM ${num}`;
            // CRM presente indica laudo médico — boost leve em categorias que exigem laudo
            ['bpc', 'ciptea', 'plano_saude', 'sus_terapias', 'transporte', 'trabalho', 'fgts'].forEach((catId) => {
                if (scores[catId]) {
                    scores[catId].score += 2;
                    scores[catId].matches.add(crmLabel);
                }
            });
        }

        // ── Pass 1: KEYWORD_MAP (highest signal) ──
        // Dedup: se variantes acentuadas normalizam à mesma chave, só contar uma vez
        const seenNormalized = new Set();
        for (const [keyword, { cats, weight }] of Object.entries(KEYWORD_MAP)) {
            const normalizedKey = normalizeText(keyword);
            if (seenNormalized.has(normalizedKey)) continue;
            seenNormalized.add(normalizedKey);
            let matchCount;

            if (UPPERCASE_ONLY_TERMS.has(normalizedKey)) {
                // Sigla/código: só casa em MAIÚSCULAS no texto original.
                // Usa (?:^|[\s,.;:()\[\]/\-]) em vez de \b para suportar
                // texto com acentos (\b é ASCII-only) — cross-browser safe.
                const upperKey = keyword.toUpperCase();
                const safeB = '(?:^|[\\s,.;:()\\[\\]/\\-])';
                const safeA = '(?=$|[\\s,.;:()\\[\\]/\\-])';
                const regex = new RegExp(safeB + escapeRegex(upperKey) + safeA, 'g');
                matchCount = (rawText.match(regex) || []).length;
            } else {
                // Termo regular: word-boundary no texto normalizado
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

        // ── Pass 2: Match against category tags ──
        direitosData.forEach((cat) => {
            (cat.tags || []).forEach((tag) => {
                const normalizedTag = normalizeText(tag);

                // Respeitar UPPERCASE_ONLY_TERMS também em tags
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

                // Usar word boundary para tags curtas, includes para longas
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

        // ── Pass 3: Match against category requisitos ──
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

        // Build results array, sorted by score
        return direitosData
            .map((cat) => ({
                category: cat,
                score: scores[cat.id].score,
                matches: Array.from(scores[cat.id].matches),
            }))
            .filter((r) => r.score > 0)
            .sort((a, b) => b.score - a.score);
    }

    /**
     * Renderiza os resultados da análise no painel.
     * @param {Array} results — resultado do matchRights
     * @param {string|string[]} fileNames — nome(s) do(s) arquivo(s) analisado(s)
     * @param {boolean} hasPdf — se ao menos um PDF foi analisado
     * @param {Array} [errors=[]] — arquivos que falharam na extração
     */
    function renderAnalysisResults(results, fileNames, hasPdf, errors = []) {
        // Normalize to array for backward compat
        const names = Array.isArray(fileNames) ? fileNames : [fileNames];
        const fileCount = names.length;
        const filesLabel = fileCount === 1
            ? `📄 Arquivo analisado: <strong>${escapeHtml(names[0])}</strong>`
            : `📄 ${fileCount} arquivos analisados: ${names.map((n) => `<strong>${escapeHtml(n)}</strong>`).join(', ')}`;

        if (results.length === 0) {
            dom.analysisContent.innerHTML = `
                <div class="analysis-empty">
                    <p>${filesLabel}</p>
                    <p>Não foram encontradas correspondências claras com as categorias de direitos.</p>
                    ${!hasPdf ? `<p class="analysis-hint">💡 Para imagens, a análise é limitada ao nome do arquivo.
                        Faça upload do <strong>PDF do laudo</strong> para uma análise mais completa.</p>` : ''}
                    ${errors.length ? `<div class="analysis-errors-summary">
                        <p>⚠️ Alguns arquivos não puderam ser processados:</p>
                        ${errors.map((e) => `<p class="analysis-hint">· ${escapeHtml(e.name)}: ${escapeHtml(e.reason)}</p>`).join('')}
                    </div>` : ''}
                    <p class="analysis-hint">💡 Navegue pelas <a href="#categorias">categorias</a> para encontrar
                        seus direitos manualmente, ou use a <a href="#busca">busca</a>.</p>
                </div>`;
            return;
        }

        const maxScore = results[0].score;

        let html = `
            <div class="analysis-file-info">
                <p>${filesLabel}</p>
                <p class="analysis-privacy">🔒 Análise 100% local — nenhum dado foi enviado para servidores.</p>
                ${errors.length ? `<p class="analysis-errors-inline">⚠️ ${errors.length} arquivo(s) com erro: ${errors.map((e) => escapeHtml(e.name)).join(', ')}</p>` : ''}
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
            // Barra visual: alta=85-100%, média=45-70%, baixa=15-35%
            const barPct = level === 'high' ? Math.max(85, pct) : level === 'medium' ? Math.round(45 + (pct - 40) * 0.625) : Math.round(15 + pct * 0.5);

            html += `
                <div class="analysis-match ${level}" data-cat-id="${category.id}" aria-label="${levelLabel}">
                    <div class="analysis-match-header">
                        <span class="analysis-match-icon">${category.icone}</span>
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
                // CID: só exibe se houver número
                if (m.startsWith('CID')) {
                    const cidNum = m.match(/CID\s+([A-Z0-9.]+)/);
                    return cidNum ? `<span class="kw-tag ${level}">${escapeHtml(m)}</span>` : `<span class="kw-tag low">CID não identificado</span>`;
                }
                // CRM: só exibe se houver número
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
            <div class="analysis-footer">
                <p>⚠️ <strong>Atenção:</strong> Esta análise é uma <strong>orientação preliminar</strong>
                baseada em correspondência de palavras-chave. <strong>Não substitui</strong> orientação
                profissional. Para confirmação, procure a <strong>Defensoria Pública</strong>,
                um advogado ou o <strong>CRAS</strong> da sua cidade.</p>
            </div>`;

        dom.analysisContent.innerHTML = html;

        // Bind "Ver detalhes" buttons
        dom.analysisContent.querySelectorAll('.analysis-see-more').forEach((btn) => {
            btn.addEventListener('click', () => {
                showDetalhe(btn.dataset.id);
                dom.analysisResults.style.display = 'none';
            });
        });
    }

    // ========================
    // Crypto — AES-GCM-256 (Web Crypto API)
    // ========================

    /**
     * Retrieves or generates the AES-256-GCM master key.
     * Key is non-exportable and stored in IndexedDB crypto_keys store.
     * Protects against: forensic recovery, browser extension snooping,
     * raw DB file inspection, cross-origin access.
     */
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
            // JWK fallback (Safari 12-14)
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

        // Generate new non-exportable AES-256-GCM key
        // Use exportable key + JWK storage as fallback for Safari 12-14
        // (older Safari can't structured-clone non-exportable CryptoKey into IndexedDB)
        let exportable = false;
        let key;
        try {
            key = await crypto.subtle.generateKey(
                { name: 'AES-GCM', length: 256 },
                false, // non-exportable — CWE-326 mitigation
                ['encrypt', 'decrypt']
            );
            // Test if we can store it in IndexedDB
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
            // Safari 12-14: DataCloneError — fallback to exportable key stored as JWK
            console.warn('[Crypto] CryptoKey structured clone failed, using JWK fallback:', cloneErr.message);
            exportable = true;
            key = await crypto.subtle.generateKey(
                { name: 'AES-GCM', length: 256 },
                true, // exportable for JWK storage
                ['encrypt', 'decrypt']
            );
        }

        // JWK fallback path for Safari 12-14
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

    /**
     * Encrypts an ArrayBuffer with AES-256-GCM.
     * Returns { ciphertext: ArrayBuffer, iv: Uint8Array }
     */
    async function encryptBuffer(plainBuffer) {
        const key = await getCryptoKey();
        if (!key) {
            // Fallback: return unencrypted if crypto unavailable (file:// protocol)
            return { ciphertext: plainBuffer, iv: null };
        }

        const iv = crypto.getRandomValues(new Uint8Array(12)); // 96-bit IV per NIST SP 800-38D
        const ciphertext = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv, tagLength: 128 },
            key,
            plainBuffer
        );

        return { ciphertext, iv: Array.from(iv) }; // iv as plain array for IndexedDB storage
    }

    /**
     * Decrypts file data. Handles both encrypted (v2) and legacy unencrypted (v1) files.
     */
    async function decryptFileData(fileObj) {
        // Legacy unencrypted file (pre-v2)
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
            // Fallback: try returning raw data (may be unencrypted legacy)
            return fileObj.data;
        }
    }

    // ========================
    // File TTL — Auto-expiration
    // ========================

    /**
     * Removes files past their TTL. Runs on boot + every 60s.
     * OWASP A05:2021 — limits data retention window.
     * @returns {number} Number of files removed
     */
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

    // ========================
    // IndexedDB Operations
    // ========================
    function openDB() {
        return new Promise((resolve, reject) => {
            const req = indexedDB.open(DB_NAME, DB_VERSION);

            req.onupgradeneeded = (e) => {
                const db = e.target.result;

                // v1: Create documents store
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME, { keyPath: 'id' });
                }

                // v2: Create crypto key store
                if (!db.objectStoreNames.contains(CRYPTO_STORE)) {
                    db.createObjectStore(CRYPTO_STORE, { keyPath: 'id' });
                }
            };

            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
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

    // ========================
    // Footer
    // ========================
    function setupFooter() {
        if (dom.lastUpdate && !dom.lastUpdate.textContent) {
            dom.lastUpdate.textContent = new Date().toLocaleDateString('pt-BR');
        }
    }

    /**
     * Called after loadData() so jsonMeta is available.
     */
    function setupFooterVersion() {
        if (dom.footerVersion && jsonMeta && jsonMeta.versao) {
            dom.footerVersion.textContent = `v${jsonMeta.versao}`;
            dom.footerVersion.title = `Versão dos dados: ${jsonMeta.versao}`;
        }
    }

    // ========================
    // Local Storage Helpers
    // ========================
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
            // Silently fail — privacy mode etc.
        }
    }

    // ========================
    // Utility Functions
    // ========================

    /**
     * Validates a URL is safe to navigate to (CWE-601 — Open Redirect prevention).
     * Allows: same-origin, gov.br domains, blob:, tel:, mailto:, and anchor links.
     * Rejects: javascript:, data: (non-image), and unknown external destinations.
     * @param {string} url - URL to validate
     * @returns {boolean} true if safe
     */
    function isSafeUrl(url) {
        if (!url || typeof url !== 'string') return false;
        const trimmed = url.trim().toLowerCase();

        // Block dangerous protocols
        if (trimmed.startsWith('javascript:') || trimmed.startsWith('vbscript:')) return false;

        // Allow: anchor links, relative paths, blob:, tel:, mailto:
        if (trimmed.startsWith('#') || trimmed.startsWith('/') || trimmed.startsWith('./')) return true;
        if (trimmed.startsWith('blob:') || trimmed.startsWith('tel:') || trimmed.startsWith('mailto:')) return true;

        // Allow: same-origin and trusted domains
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

    // Reusable element for escapeHtml — avoids creating a new DOM node per call
    const _escapeDiv = document.createElement('div');

    function escapeHtml(str) {
        if (!str) return '';
        _escapeDiv.textContent = str;
        return _escapeDiv.innerHTML;
    }

    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function normalizeText(text) {
        return text
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '');
    }

    function formatDate(dateStr) {
        try {
            const d = new Date(dateStr + 'T00:00:00');
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

    /**
     * Formats remaining time until expiration in human-readable PT-BR.
     */
    function formatTimeRemaining(expiresAt) {
        const diff = new Date(expiresAt).getTime() - Date.now();
        if (diff <= 0) return 'Expirado';
        const mins = Math.ceil(diff / 60000);
        if (mins < 60) return `Expira em ${mins} min`;
        const hours = Math.floor(mins / 60);
        const remMins = mins % 60;
        return `Expira em ${hours}h${remMins > 0 ? remMins + 'min' : ''}`;
    }

    // ========================
    // Boot
    // ========================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
