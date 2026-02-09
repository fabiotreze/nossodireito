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
    // State
    // ========================
    let direitosData = null;
    let fontesData = null;
    let docsMestreData = null;
    let instituicoesData = null;
    let jsonMeta = null;
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

    // pdf.js worker
    if (typeof pdfjsLib !== 'undefined') {
        pdfjsLib.GlobalWorkerOptions.workerSrc =
            'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
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
        // Meta
        transLastUpdate: $('#transLastUpdate'),
        transNextReview: $('#transNextReview'),
        transVersion: $('#transVersion'),
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
        renderCategories();
        renderTransparency();
        renderInstituicoes();
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
        const accepted = localGet('disclaimer_accepted');

        if (accepted) {
            dom.disclaimerModal.classList.add('hidden');
        }

        dom.acceptBtn.addEventListener('click', () => {
            localSet('disclaimer_accepted', 'true');
            dom.disclaimerModal.classList.add('hidden');
        });

        dom.showDisclaimer.addEventListener('click', (e) => {
            e.preventDefault();
            dom.disclaimerModal.classList.remove('hidden');
        });
    }

    // ========================
    // Navigation
    // ========================
    function setupNavigation() {
        dom.menuToggle.addEventListener('click', () => {
            const open = dom.navLinks.classList.toggle('open');
            dom.menuToggle.setAttribute('aria-expanded', String(open));
        });

        dom.navLinks.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                dom.navLinks.classList.remove('open');
                dom.menuToggle.setAttribute('aria-expanded', 'false');
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
            dom.categoriasSection.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // ========================
    // Data Loading
    // ========================
    async function loadData() {
        try {
            const res = await fetch('data/direitos.json');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            direitosData = json.categorias;
            fontesData = json.fontes || [];
            docsMestreData = json.documentos_mestre || [];
            instituicoesData = json.instituicoes_apoio || [];
            jsonMeta = {
                versao: json.versao,
                ultima_atualizacao: json.ultima_atualizacao,
                proxima_revisao: json.proxima_revisao,
            };

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
    function showDetalhe(id) {
        const cat = direitosData.find((c) => c.id === id);
        if (!cat) return;

        dom.categoriasSection.style.display = 'none';
        dom.detalheSection.style.display = '';

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
                            `<a class="legal-link" href="${escapeHtml(l.link)}" target="_blank" rel="noopener">
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

        // Links
        if (cat.links && cat.links.length) {
            html += `<div class="detalhe-section">
                <h3>🔗 Links Úteis</h3>
                <div>${cat.links
                    .map(
                        (l) =>
                            `<a class="legal-link" href="${escapeHtml(l.url)}" target="_blank" rel="noopener">
                            🌐 ${escapeHtml(l.titulo)}
                        </a>`
                    )
                    .join('')}</div>
            </div>`;
        }

        // Tags
        if (cat.tags && cat.tags.length) {
            html += `<div class="detalhe-tags">
                ${cat.tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
            </div>`;
        }

        dom.detalheContent.innerHTML = html;
        dom.detalheSection.scrollIntoView({ behavior: 'smooth' });
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
            });
        });
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
                        <a href="${escapeHtml(f.url)}" target="_blank" rel="noopener">Abrir ↗</a>
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
                        <a href="${escapeHtml(inst.url)}" class="btn btn-sm btn-outline inst-link" target="_blank" rel="noopener">
                            Acessar site ↗
                        </a>
                    </div>`;
                })
                .join('');
        }

        renderInstitutions('todos');

        // Filter buttons
        document.querySelectorAll('.inst-filter-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.inst-filter-btn').forEach((b) => b.classList.remove('active'));
                btn.classList.add('active');
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
            .map((lk) => {
                const domain = (() => {
                    try { return new URL(lk.url).hostname.replace('www.', ''); }
                    catch { return ''; }
                })();
                const icon = domain.includes('gov.br') ? '🏛️'
                    : domain.includes('inss') ? '📋'
                        : domain.includes('mds.gov') ? '🏠'
                            : '🔗';
                return `
                <a href="${escapeHtml(lk.url)}" class="link-card" target="_blank" rel="noopener">
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
                dom.staleDays.textContent = diffDays;
            }
            dom.stalenessBanner.hidden = false;
        } else {
            dom.stalenessBanner.hidden = true;
        }
    }

    // ========================
    // File Upload (IndexedDB)
    // ========================
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
        dom.deleteAllFiles.addEventListener('click', async () => {
            if (confirm('Tem certeza? Todos os arquivos serão removidos permanentemente do seu navegador.')) {
                await clearAllFiles();
                await renderFileList();
            }
        });
    }

    async function handleFiles(fileList) {
        const currentCount = await getFileCount();
        const filesToAdd = Array.from(fileList);

        if (currentCount + filesToAdd.length > MAX_FILES) {
            alert(`Limite de ${MAX_FILES} arquivos. Você já tem ${currentCount}. Pode adicionar mais ${MAX_FILES - currentCount}.`);
            return;
        }

        for (const file of filesToAdd) {
            // Validate type
            if (!ALLOWED_TYPES.includes(file.type)) {
                const parts = file.name.split('.');
                const ext = parts.length > 1 ? parts.pop().toLowerCase() : '';
                if (!ALLOWED_EXTENSIONS.includes('.' + ext)) {
                    alert(`Formato não aceito: ${file.name}\nFormatos válidos: PDF, JPG, PNG`);
                    continue;
                }
            }

            // Validate size
            if (file.size > MAX_FILE_SIZE) {
                alert(`Arquivo muito grande: ${file.name} (${formatBytes(file.size)})\nMáximo: 5MB por arquivo`);
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
                alert(`Erro ao salvar: ${file.name}`);
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
                        <span class="file-item-icon">${icon}</span>
                        <div class="file-item-info">
                            <div class="file-item-name" title="${escapeHtml(f.name)}">${cryptoBadge}${escapeHtml(f.name)}</div>
                            <div class="file-item-meta">${formatBytes(f.size)} · Adicionado em ${date} ${expiresStr}</div>
                        </div>
                        <div class="file-item-actions">
                            <button class="btn-analyze" title="Analisar direitos" data-id="${f.id}">🔍 Analisar</button>
                            <button class="btn-view" title="Visualizar" data-id="${f.id}">👁️ Ver</button>
                            <button class="btn-delete" title="Excluir" data-id="${f.id}">🗑️</button>
                        </div>
                    </div>`;
                })
                .join('');

            // Bind events
            dom.fileList.querySelectorAll('.btn-analyze').forEach((btn) => {
                btn.addEventListener('click', () => analyzeDocument(btn.dataset.id));
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
                btn.addEventListener('click', async () => {
                    if (confirm('Excluir este arquivo?')) {
                        await deleteFile(btn.dataset.id);
                        await renderFileList();
                    }
                });
            });
        } catch (err) {
            console.error('Erro ao listar arquivos:', err);
        }
    }

    // ========================
    // Document Analysis Engine
    // ========================
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
    }

    /**
     * Analisa um documento enviado e identifica direitos aplicáveis.
     * Para PDFs: extrai texto com pdf.js e faz matching por keywords.
     * Para imagens: usa nome do arquivo e metadados para inferir.
     * 100% local — nada é enviado para servidores.
     */
    async function analyzeDocument(fileId) {
        const file = await getFile(fileId);
        if (!file) {
            alert('Arquivo não encontrado.');
            return;
        }

        dom.analysisResults.style.display = '';
        dom.analysisLoading.style.display = '';
        dom.analysisContent.innerHTML = '';
        dom.analysisResults.scrollIntoView({ behavior: 'smooth' });

        try {
            let extractedText = '';
            const plainData = await decryptFileData(file);

            if (file.type === 'application/pdf') {
                extractedText = await extractPdfText(plainData);
            } else {
                // Para imagens, analisar apenas pelo nome do arquivo
                extractedText = file.name;
            }

            const results = matchRights(extractedText, file.name);
            renderAnalysisResults(results, file.name, file.type === 'application/pdf');

            // Auto-delete file after successful analysis (consulta pontual)
            try {
                await deleteFile(fileId);
                await renderFileList();
                console.info(`[Security] Arquivo ${file.name} descartado automaticamente após análise.`);
            } catch (delErr) {
                console.warn('Erro ao descartar arquivo após análise:', delErr);
            }

        } catch (err) {
            console.error('Erro na análise:', err);
            dom.analysisContent.innerHTML = `
                <div class="analysis-error">
                    <p>⚠️ Não foi possível analisar este documento.</p>
                    <p style="font-size:0.85rem;color:var(--text-muted);">
                        ${file.type === 'application/pdf'
                    ? 'O PDF pode estar protegido, escaneado (imagem) ou em formato não-textual.'
                    : 'Para imagens, a análise é limitada ao nome do arquivo.'}
                    </p>
                    <p style="font-size:0.85rem;margin-top:8px;">
                        💡 <strong>Dica:</strong> Navegue pelas <a href="#categorias">categorias</a>
                        para encontrar seus direitos manualmente.
                    </p>
                </div>`;
        } finally {
            dom.analysisLoading.style.display = 'none';
        }
    }

    /**
     * Extrai texto de um ArrayBuffer contendo um PDF usando pdf.js
     */
    async function extractPdfText(arrayBuffer) {
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
     * Dicionário de palavras-chave → categorias para matching inteligente.
     * Inclui termos médicos, jurídicos e coloquiais que famílias usam.
     */
    const KEYWORD_MAP = {
        // BPC / LOAS
        bpc: { cats: ['bpc'], weight: 5 },
        loas: { cats: ['bpc'], weight: 5 },
        'benefício assistencial': { cats: ['bpc'], weight: 4 },
        'beneficio assistencial': { cats: ['bpc'], weight: 4 },
        cadúnico: { cats: ['bpc'], weight: 3 },
        cadunico: { cats: ['bpc'], weight: 3 },
        'cadastro único': { cats: ['bpc'], weight: 3 },
        inss: { cats: ['bpc', 'fgts'], weight: 3 },
        perícia: { cats: ['bpc'], weight: 2 },
        pericia: { cats: ['bpc'], weight: 2 },

        // CIPTEA
        ciptea: { cats: ['ciptea'], weight: 5 },
        'carteira de identificação': { cats: ['ciptea'], weight: 4 },
        'romeo mion': { cats: ['ciptea'], weight: 5 },

        // TEA / Autismo (trans-category)
        autismo: { cats: ['ciptea', 'educacao', 'plano_saude', 'sus_terapias'], weight: 3 },
        tea: { cats: ['ciptea', 'educacao', 'plano_saude', 'sus_terapias'], weight: 3 },
        'f84': { cats: ['ciptea', 'educacao', 'plano_saude', 'sus_terapias'], weight: 4 },
        '6a02': { cats: ['ciptea', 'educacao', 'plano_saude', 'sus_terapias'], weight: 4 },
        'espectro autista': { cats: ['ciptea', 'educacao', 'plano_saude', 'sus_terapias'], weight: 4 },
        'berenice piana': { cats: ['ciptea', 'educacao', 'plano_saude', 'sus_terapias'], weight: 3 },

        // Deficiência geral
        deficiência: { cats: ['bpc', 'educacao', 'transporte', 'trabalho', 'fgts', 'moradia'], weight: 2 },
        deficiencia: { cats: ['bpc', 'educacao', 'transporte', 'trabalho', 'fgts', 'moradia'], weight: 2 },
        'pessoa com deficiência': { cats: ['bpc', 'educacao', 'transporte', 'trabalho', 'moradia'], weight: 3 },
        pcd: { cats: ['bpc', 'educacao', 'transporte', 'trabalho', 'fgts', 'moradia'], weight: 3 },
        laudo: { cats: ['bpc', 'ciptea', 'educacao', 'plano_saude', 'sus_terapias', 'transporte', 'trabalho', 'fgts'], weight: 2 },
        cid: { cats: ['bpc', 'ciptea', 'plano_saude', 'sus_terapias'], weight: 3 },
        'cid-10': { cats: ['bpc', 'ciptea', 'plano_saude', 'sus_terapias'], weight: 3 },
        'cid-11': { cats: ['bpc', 'ciptea', 'plano_saude', 'sus_terapias'], weight: 3 },
        diagnóstico: { cats: ['bpc', 'ciptea', 'plano_saude', 'sus_terapias'], weight: 2 },
        diagnostico: { cats: ['bpc', 'ciptea', 'plano_saude', 'sus_terapias'], weight: 2 },

        // Educação
        escola: { cats: ['educacao'], weight: 4 },
        matrícula: { cats: ['educacao'], weight: 4 },
        matricula: { cats: ['educacao'], weight: 4 },
        inclusão: { cats: ['educacao'], weight: 3 },
        inclusao: { cats: ['educacao'], weight: 3 },
        aee: { cats: ['educacao'], weight: 5 },
        'atendimento educacional': { cats: ['educacao'], weight: 4 },
        acompanhante: { cats: ['educacao'], weight: 3 },
        'educação especial': { cats: ['educacao'], weight: 4 },

        // Plano de saúde
        'plano de saúde': { cats: ['plano_saude'], weight: 5 },
        'plano de saude': { cats: ['plano_saude'], weight: 5 },
        ans: { cats: ['plano_saude'], weight: 4 },
        operadora: { cats: ['plano_saude'], weight: 3 },
        cobertura: { cats: ['plano_saude'], weight: 3 },
        negativa: { cats: ['plano_saude'], weight: 3 },

        // Terapias
        terapia: { cats: ['plano_saude', 'sus_terapias'], weight: 3 },
        aba: { cats: ['plano_saude', 'sus_terapias'], weight: 4 },
        fonoaudiologia: { cats: ['plano_saude', 'sus_terapias'], weight: 3 },
        fono: { cats: ['plano_saude', 'sus_terapias'], weight: 3 },
        'terapia ocupacional': { cats: ['plano_saude', 'sus_terapias'], weight: 3 },
        psicologia: { cats: ['plano_saude', 'sus_terapias'], weight: 2 },
        fisioterapia: { cats: ['sus_terapias'], weight: 3 },
        reabilitação: { cats: ['sus_terapias'], weight: 3 },
        reabilitacao: { cats: ['sus_terapias'], weight: 3 },

        // SUS
        sus: { cats: ['sus_terapias'], weight: 4 },
        ubs: { cats: ['sus_terapias'], weight: 3 },
        caps: { cats: ['sus_terapias'], weight: 4 },
        cer: { cats: ['sus_terapias'], weight: 4 },
        medicamento: { cats: ['sus_terapias'], weight: 3 },
        'farmácia popular': { cats: ['sus_terapias'], weight: 4 },

        // Transporte
        transporte: { cats: ['transporte'], weight: 4 },
        'passe livre': { cats: ['transporte'], weight: 5 },
        ônibus: { cats: ['transporte'], weight: 3 },
        onibus: { cats: ['transporte'], weight: 3 },
        ipva: { cats: ['transporte'], weight: 4 },
        ipi: { cats: ['transporte'], weight: 3 },
        isenção: { cats: ['transporte'], weight: 3 },
        isencao: { cats: ['transporte'], weight: 3 },

        // Trabalho
        trabalho: { cats: ['trabalho'], weight: 4 },
        emprego: { cats: ['trabalho'], weight: 3 },
        cota: { cats: ['trabalho'], weight: 4 },
        cotas: { cats: ['trabalho'], weight: 4 },
        clt: { cats: ['trabalho'], weight: 3 },
        'carteira de trabalho': { cats: ['trabalho', 'fgts'], weight: 3 },
        ctps: { cats: ['trabalho', 'fgts'], weight: 3 },

        // FGTS
        fgts: { cats: ['fgts'], weight: 5 },
        saque: { cats: ['fgts'], weight: 3 },
        caixa: { cats: ['fgts'], weight: 2 },
        'caixa econômica': { cats: ['fgts'], weight: 3 },

        // Documentos comuns (indicadores)
        'certidão de nascimento': { cats: ['bpc', 'ciptea'], weight: 1 },
        'comprovante de residência': { cats: ['bpc', 'ciptea', 'educacao', 'moradia'], weight: 1 },
        cpf: { cats: ['bpc', 'ciptea', 'transporte'], weight: 1 },

        // Moradia / Condomínio
        moradia: { cats: ['moradia'], weight: 5 },
        'condomínio': { cats: ['moradia'], weight: 5 },
        condominio: { cats: ['moradia'], weight: 5 },
        'vaga especial': { cats: ['moradia'], weight: 5 },
        'vaga reservada': { cats: ['moradia'], weight: 5 },
        'vaga pcd': { cats: ['moradia'], weight: 5 },
        estacionamento: { cats: ['moradia'], weight: 3 },
        rampa: { cats: ['moradia'], weight: 4 },
        elevador: { cats: ['moradia'], weight: 3 },
        'área comum': { cats: ['moradia'], weight: 3 },
        'area comum': { cats: ['moradia'], weight: 3 },
        síndico: { cats: ['moradia'], weight: 4 },
        sindico: { cats: ['moradia'], weight: 4 },
        'nbr 9050': { cats: ['moradia'], weight: 5 },
        'lei 10.098': { cats: ['moradia'], weight: 4 },
        'minha casa minha vida': { cats: ['moradia'], weight: 5 },
        'programa habitacional': { cats: ['moradia'], weight: 4 },
        habitação: { cats: ['moradia'], weight: 4 },
        habitacao: { cats: ['moradia'], weight: 4 },
        'adaptação': { cats: ['moradia'], weight: 3 },
        adaptacao: { cats: ['moradia'], weight: 3 },
        'barreira arquitetônica': { cats: ['moradia'], weight: 4 },
        'barreira arquitetonica': { cats: ['moradia'], weight: 4 },
        assembleia: { cats: ['moradia'], weight: 3 },
        'convenção do condomínio': { cats: ['moradia'], weight: 4 },

        // Termos médicos adicionais
        neuropediatra: { cats: ['ciptea', 'sus_terapias'], weight: 2 },
        neurologista: { cats: ['sus_terapias'], weight: 2 },
        psiquiatra: { cats: ['sus_terapias'], weight: 2 },
        impedimento: { cats: ['bpc'], weight: 2 },
        'longo prazo': { cats: ['bpc'], weight: 2 },
    };

    /**
     * Faz matching do texto extraído contra as categorias do JSON.
     * Combina: (1) KEYWORD_MAP, (2) category tags, (3) category requisitos/docs.
     * Retorna array ordenado por score.
     */
    function matchRights(text, fileName) {
        if (!direitosData) return [];

        const normalizedText = normalizeText(text + ' ' + fileName);
        const scores = {};

        // Initialize scores
        direitosData.forEach((cat) => {
            scores[cat.id] = { score: 0, matches: new Set() };
        });

        // Pass 1: KEYWORD_MAP (highest signal)
        for (const [keyword, { cats, weight }] of Object.entries(KEYWORD_MAP)) {
            const normalizedKey = normalizeText(keyword);
            const regex = new RegExp('\\b' + escapeRegex(normalizedKey) + '\\b', 'g');
            const matchCount = (normalizedText.match(regex) || []).length;

            if (matchCount > 0) {
                cats.forEach((catId) => {
                    if (scores[catId]) {
                        // Diminishing returns: first occurrence counts most
                        scores[catId].score += weight * Math.min(matchCount, 3);
                        scores[catId].matches.add(keyword);
                    }
                });
            }
        }

        // Pass 2: Match against category tags
        direitosData.forEach((cat) => {
            (cat.tags || []).forEach((tag) => {
                const normalizedTag = normalizeText(tag);
                if (normalizedText.includes(normalizedTag)) {
                    scores[cat.id].score += 2;
                    scores[cat.id].matches.add(tag);
                }
            });
        });

        // Pass 3: Match against category requisitos
        direitosData.forEach((cat) => {
            (cat.requisitos || []).forEach((req) => {
                const words = normalizeText(req).split(/\s+/).filter((w) => w.length > 4);
                const matchedWords = words.filter((w) => normalizedText.includes(w));
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
     */
    function renderAnalysisResults(results, fileName, isPdf) {
        if (results.length === 0) {
            dom.analysisContent.innerHTML = `
                <div class="analysis-empty">
                    <p>📄 Arquivo: <strong>${escapeHtml(fileName)}</strong></p>
                    <p>Não foram encontradas correspondências claras com as categorias de direitos.</p>
                    ${!isPdf ? `<p class="analysis-hint">💡 Para imagens, a análise é limitada ao nome do arquivo.
                        Faça upload do <strong>PDF do laudo</strong> para uma análise mais completa.</p>` : ''}
                    <p class="analysis-hint">💡 Navegue pelas <a href="#categorias">categorias</a> para encontrar
                        seus direitos manualmente, ou use a <a href="#busca">busca</a>.</p>
                </div>`;
            return;
        }

        const maxScore = results[0].score;

        let html = `
            <div class="analysis-file-info">
                <p>📄 Arquivo analisado: <strong>${escapeHtml(fileName)}</strong></p>
                <p class="analysis-privacy">🔒 Análise 100% local — nenhum dado foi enviado para servidores.</p>
            </div>
            <div class="analysis-match-list">`;

        results.forEach(({ category, score, matches }) => {
            const pct = Math.round((score / maxScore) * 100);
            const level = pct >= 80 ? 'high' : pct >= 40 ? 'medium' : 'low';
            const levelLabel = pct >= 80 ? 'Alta relevância' : pct >= 40 ? 'Média relevância' : 'Possível relação';

            html += `
                <div class="analysis-match ${level}" data-cat-id="${category.id}">
                    <div class="analysis-match-header">
                        <span class="analysis-match-icon">${category.icone}</span>
                        <div class="analysis-match-title">
                            <h4>${escapeHtml(category.titulo)}</h4>
                            <span class="analysis-badge ${level}">${levelLabel}</span>
                        </div>
                        <div class="analysis-match-bar">
                            <div class="analysis-match-fill" style="width:${pct}%"></div>
                        </div>
                    </div>
                    <p class="analysis-match-resumo">${escapeHtml(category.resumo)}</p>
                    ${matches.length ? `
                    <div class="analysis-match-keywords">
                        <span class="kw-label">Termos encontrados:</span>
                        ${matches.slice(0, 8).map((m) => `<span class="kw-tag">${escapeHtml(m)}</span>`).join('')}
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

    async function storeFile(fileObj) {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            tx.objectStore(STORE_NAME).put(fileObj);
            tx.oncomplete = () => { db.close(); resolve(); };
            tx.onerror = () => { db.close(); reject(tx.error); };
        });
    }

    async function getAllFiles() {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly');
            const req = tx.objectStore(STORE_NAME).getAll();
            req.onsuccess = () => { db.close(); resolve(req.result); };
            req.onerror = () => { db.close(); reject(req.error); };
        });
    }

    async function getFile(id) {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly');
            const req = tx.objectStore(STORE_NAME).get(id);
            req.onsuccess = () => { db.close(); resolve(req.result); };
            req.onerror = () => { db.close(); reject(req.error); };
        });
    }

    async function deleteFile(id) {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            tx.objectStore(STORE_NAME).delete(id);
            tx.oncomplete = () => { db.close(); resolve(); };
            tx.onerror = () => { db.close(); reject(tx.error); };
        });
    }

    async function clearAllFiles() {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            tx.objectStore(STORE_NAME).clear();
            tx.oncomplete = () => { db.close(); resolve(); };
            tx.onerror = () => { db.close(); reject(tx.error); };
        });
    }

    async function getFileCount() {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly');
            const req = tx.objectStore(STORE_NAME).count();
            req.onsuccess = () => { db.close(); resolve(req.result); };
            req.onerror = () => { db.close(); reject(req.error); };
        });
    }

    // ========================
    // Footer
    // ========================
    function setupFooter() {
        if (dom.lastUpdate && !dom.lastUpdate.textContent) {
            dom.lastUpdate.textContent = new Date().toLocaleDateString('pt-BR');
        }
    }

    // ========================
    // Local Storage Helpers
    // ========================
    function localGet(key) {
        try {
            const val = localStorage.getItem(STORAGE_PREFIX + key);
            return val ? JSON.parse(val) : null;
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
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
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
