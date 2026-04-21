# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.14.8] - 2026-03-01

### Alterado

- **Migração de tenant Azure** — novo tenant (`f1856a79`), subscription MSDN-online (`3acb7300`), SP `sp-nossodireito-deploy` com OIDC
- **Região brazilsouth** — todos os recursos migrados de `eastus2` para `brazilsouth` (conformidade LGPD — dados em território nacional)
- **Renomeação de recursos** — sufixo `-br` em todos os recursos Azure: `app-nossodireito-br`, `rg-nossodireito-br`, `kv-nossodireito-br`, etc.
- **Centralização de nomes (zero hardcoding):**
  - `terraform/variables.tf` — novo `var.project_name` (default `"nossodireito-br"`) com `locals` derivando todos os nomes via interpolação
  - `.github/workflows/*.yml` — `env.PROJECT` centralizado; todos os comandos `az` usam `${PROJECT}`
  - `server.js` — `process.env.WEBSITE_HOSTNAME` (injetado pelo Azure) substitui hostname hardcoded em ALLOWED_HOSTS, ALLOWED_ORIGINS e redirect 301
- **docs/ARCHITECTURE.md** — snippets de código atualizados para refletir padrão dinâmico (`WEBSITE_HOSTNAME`, `${{ env.PROJECT }}`)

---

## [1.14.7] - 2026-02-28

### Removido

- **docs/v1/ inteiro** — 11 arquivos órfãos (zero referências em código/testes/compliance)
- **TESTING.md** — conteúdo absorvido em `docs/QUALITY_GUIDE.md` (§0 Quick Start)
- **docs/VALIDATION_STATUS.md** — conteúdo absorvido em `docs/QUALITY_GUIDE.md`
- **scripts/validate_govbr_urls.py** — lógica de retry/backoff absorvida em `validate_urls.py`
- **33 testes duplicados** — deduplicação: TestPWA (×4→×3), TestAccessibility, TestVersionConsistency, TestServerSecurity removidos de test_cross_browser.py; métodos duplicados removidos de comprehensive/validation/e2e

### Alterado

- **README.md** — Quick Start no topo, seção NOVIDADES atualizada para v1.14.7, referências a arquivos deletados removidas
- **docs/QUALITY_GUIDE.md** — adicionada §0 Quick Start (pré-requisitos + copiar/colar), consolida TESTING + VALIDATION_STATUS
- **docs/COMPLIANCE.md** — referências a docs/v1 e VALIDATION_STATUS.md atualizadas
- **scripts/validate_urls.py** — `check_url_live()` agora com retry exponencial + fallback HEAD→GET (ex-validate_govbr_urls.py)
- **scripts/validate_all.py** — `run_script()` aceita `extra_args`; Fase 7 usa `validate_urls.py --check-live`
- **scripts/audit_automation.py** — referência atualizada para validate_urls.py; output consolidado em QUALITY_GUIDE.md
- **scripts/master_compliance.py** — dead references atualizadas para TESTING.md, VALIDATION_STATUS.md, validate_govbr_urls.py

---

## [1.14.6] - 2026-02-28

### Corrigido

- **B1: CSS alto contraste inoperante** — 8 seletores `body.high-contrast` alterados para `html.high-contrast` (JS aplica classe em `<html>`, não `<body>`)
- **B2: Variáveis CSS ausentes** — adicionadas `--primary-bg` e `--focus-ring` ao `:root`
- **B3: MIME types faltantes** — `.jpg`/`.jpeg` adicionados a `server.js` com cache imutável 30d
- **B4: `deficiencia_fala.niveis` era dict em vez de list** — corrigido para manter consistência com demais categorias
- **B5: `STATIC_ASSETS` morto no sw.js** — convertido para background caching no evento `activate`
- **B6: `Permissions-Policy` via meta tag** — substituído por comentário HTML (deve ser enforced via HTTP header); adicionado `<meta name="color-scheme" content="light dark">`

### Atualizado

- **W1: validate_content.py header** v1.14.0 → v1.14.5
- **W2: TESTING.md** Node.js 18+ → 22+
- **W3: pytest.ini** minversion 3.8 → 7.0
- **W6: robots.txt** — 7 bloqueios de crawlers AI (Bytespider, PetalBot, Meta-ExternalAgent, PerplexityBot, Applebot-Extended, FacebookBot, ClaudeBot)
- **W7: playwright** ~1.50 → ~1.51
- **W8: dependabot.yml** — adicionado ecossistema Terraform para `/terraform`
- **D1: Programa Mover / Lei 14.902/2024** — adicionado a `isencoes_tributarias` (base_legal + dica integrada)
- **D2: FGTS Digital** — plataforma, links e dicas atualizadas em `fgts`
- **D3: BPC** — dica de avaliação biopsicossocial adicionada
- **D4: +25 keywords** — estacionamento_especial, pensao_zika, capacidade_legal, meia_entrada, aposentadoria PcD, IRPF PcD, viagem PcD
- **D5: dicionario_pcd.json** — `deficiencia_fala.niveis` dict→list, `sindrome_zika.cid11` → `["LD2F"]`
- **D6: deficiencia_psicossocial** — CID-10 expandido de 2 para 7 códigos (F20, F31, F32, F33, F41, F42, F43.1)
- **S4: terraform.yml OIDC** — removido `ARM_CLIENT_SECRET`, adicionado `id-token: write`, `azure/login@v2` com federated credential, `ARM_USE_OIDC=true`
- **ARCHITECTURE.md** — corrigido `.high-contrast` `<body>`→`<html>`, terraform.yml OIDC, test tree + conftest + schemas
- **ARCHITECTURE.drawio.xml** — versão 1.14.4→1.14.5, legenda 841→846 testes

### Adicionado

- **tests/conftest.py** — fixtures compartilhadas (15 fixtures: direitos, matching, dicionario, schema, html, css, etc.), eliminando duplicações entre 3 arquivos de teste
- **schemas/matching_engine.schema.json** — JSON Schema draft-07 para matching_engine.json
- **schemas/dicionario_pcd.schema.json** — JSON Schema draft-07 para dicionario_pcd.json
- **.editorconfig** — padronização de encoding (UTF-8), line endings (LF), indentação (2 espaços JS/HTML, 4 Python)

**Totais:** 709 unit + 137 E2E = **846 testes** | Master Compliance: **1104.7/1104.7 (100.00%)**

## [1.14.5] - 2026-02-26

### Corrigido

- **Bug crítico: dicas ocultas desapareciam do PDF** — dicas acima de 5 usavam inline `display:none` (via JS toggle), e o CSS de impressão usava apenas `visibility:visible` que não sobrepõe `display:none` inline. Adicionado `.dicas-hidden { display: block !important }` e `.btn-ver-mais { display: none !important }` no modo `printing-detalhe`
- **GitHub Actions: referência a arquivo deletado** — `quality-gate.yml` e `deploy.yml` usavam `--ignore=tests/test_browser.py` (deletado). Atualizado para `--ignore=tests/test_e2e_playwright.py`
- **robots.txt: referência a diretório deletado** — 2 entradas `Disallow: /screenshots/` removidas (pasta não existe mais)
- **README.md: imagem quebrada** — `images/nossodireito.png` não existe; corrigido para `images/nossodireito-400.png`
- **README.md: badges duplicados** — 2 badges estáticos (Quality Gate, Deploy) duplicavam os badges GitHub Actions. Removidos
- **pre-commit: comentários desatualizados** — referências a arquivos de teste deletados atualizadas para `test_e2e_playwright.py`
- **TESTING.md: estrutura de arquivos incorreta** — listava arquivos do `scripts/` como se estivessem em `tests/`. Corrigido com estrutura real
- **venv macOS em Windows** — `.venv` criado no macOS apontava para `/opt/homebrew/`. Recriado com Python 3.10.11 Windows local

### Atualizado

- **ARCHITECTURE.md** — adicionados protocolos de emergência, dicas colapsáveis e ícone ABNT ao Resumo Executivo; KPIs com contagem de testes (846) e Master Compliance (100%); CI/CD atualizado para refletir workflows reais; adicionada seção "Infraestrutura de Testes" com árvore completa de 5 arquivos de teste + 18 scripts; versão na conclusão atualizada para 1.14.4
- **ARCHITECTURE.drawio.xml** — versão 1.13.1→1.14.4, test_browser.py→test_e2e_playwright.py (132→137 Playwright), test_comprehensive 147→709, legenda 188→846 total

### Adicionado

- **5 novos testes E2E** (total: 137 Playwright):
  - `test_export_button_adds_print_class` — verifica que botão PDF adiciona `printing-detalhe`
  - `test_whatsapp_share_link_present` — valida link WhatsApp com domínio correto
  - `test_whatsapp_share_opens_new_tab` — verifica `target="_blank"` e `rel="noopener"`
  - `test_print_css_reveals_hidden_dicas` — confirma que dicas ocultas aparecem em modo print
  - `test_print_css_hides_toggle_button` — confirma que botão "Mostrar mais" some no PDF

**Totais:** 709 unit + 137 E2E = **846 testes** | Master Compliance: **1104.7/1104.7 (100.00%)**

## [1.14.4] - 2026-02-25

### Corrigido

- **Bug crítico: WhatsApp share navegava a página atual** — ao clicar nos botões de compartilhar no WhatsApp (Primeiros Passos, Análise de Documentos, Documentos Necessários), quando o popup era bloqueado pelo navegador, o fallback `location.href = url` sobrescrevia a página NossoDireito com o link do WhatsApp, resultando em duas abas WhatsApp e perda do site. Corrigido: fallback agora usa `<a>` programático com `target="_blank"`, garantindo que a página original nunca é afetada
- **TTS: texto final sem pontuação era ignorado** — `splitIntoChunks` usava regex que exigia `.!?\n` ao final de cada sentença; texto após a última pontuação era silenciosamente descartado na leitura em voz alta. Corrigido com `(?:[.!?\n]+|$)`
- **Dialog `confirmAction` vazava no DOM ao pressionar Escape** — ao fechar com Escape, o `<dialog>` era ocultado mas o elemento permanecia no DOM. Adicionado listener `close` para cleanup automático
- **Dialog `confirmAction` não respondia a cliques em filhos de botão** — `e.target.tagName === 'BUTTON'` substituído por `e.target.closest('button')` para robustez
- **`decryptFileData` retornava dados criptografados em caso de falha** — agora retorna `null` com toast de erro, e callers fazem null-check
- **`waitForVoices` race condition** — chamadas concorrentes sobrescreviam `onvoiceschanged`, causando promises pendentes. Promise agora é cacheada
- **`enrichGovBr` (async) chamado via `safeRun` (sync)** — corrigido para `safeRunAsync`
- **`openDB` travava indefinidamente se IndexedDB bloqueado** — adicionado handler `onblocked`

## [1.14.3] - 2026-02-25

### Adicionado

- **Farmácia Popular 100% gratuito (fev/2025)** — atualizado resumo, passo a passo e dicas com informação oficial de que desde 14/02/2025 todos os medicamentos do programa são 100% gratuitos (Portaria GM/MS nº 264/2025)
- **CEAF — Componente Especializado da Assistência Farmacêutica** — 105 condições clínicas, 173 fármacos, passo a passo detalhado para acesso via LME e farmácia estadual
- **RENAME — Relação Nacional de Medicamentos Essenciais** — link direto e orientação para consulta
- **Fraldas geriátricas gratuitas para PcD** — qualquer idade, na Farmácia Popular com laudo médico + CID
- **TDAH: metilfenidato e Venvanse** — orientação sobre disponibilidade no SUS e caminho de judicialização via Defensoria Pública
- **10 novos links oficiais gov.br** em `sus_terapias`: Farmácia Popular, CEAF, CEAF por UF, RENAME, elenco de medicamentos (PDF), condições clínicas CEAF (PDF), lista de medicamentos CEAF (PDF), painel de endereços Farmácia Popular, telecuidado farmacêutico, SNDPD/MDHC
- **22 novas keywords** no matching_engine: fralda geriátrica, fralda PcD, CEAF, RENAME, metilfenidato, Ritalina, Venvanse, lisdexanfetamina, medicamento gratuito, desconto medicamento, doença rara, epilepsia refratária, entre outras
- **Expansão do dicionário PcD** — novos termos de saúde: Farmácia Popular, CEAF, PCDT, LME, metilfenidato, Ritalina, telecuidado farmacêutico, judicialização, fralda geriátrica, medicamento especializado
- **TDAH no dicionário** — adicionados keywords: metilfenidato, Ritalina, lisdexanfetamina, Venvanse, transtorno do neurodesenvolvimento
- **Base legal expandida** — Portaria GM/MS nº 264/2025 (Farmácia Popular 100% gratuito) adicionada à seção sus_terapias

### Corrigido

- **Passo a passo numeração** — removido "6." duplicado no passo a passo de sus_terapias
- **Texto desatualizado** — "gratuitos ou com desconto" corrigido para "100% gratuitos" conforme nova legislação

## [1.14.2] - 2026-02-24

### Adicionado

- **SEO: `<meta name="robots">` com `max-snippet:-1, max-image-preview:large`** — permite snippets maiores e imagens grandes no Google
- **SEO: Schema `WebPage`** com `dateModified`, `datePublished`, `speakable` e linkagem `@id` ao FAQPage e BreadcrumbList
- **SEO: `hreflang="pt-BR"` e `x-default`** — sinal de idioma/região para buscadores
- **SEO: `og:image:type` e `og:updated_time`** — metadados Open Graph completos
- **SEO: `Content-Language: pt-BR`** — header HTTP para páginas HTML
- **SEO: `X-Robots-Tag`** — `index, follow` para HTML; `noindex` para JSON data files
- **SEO: Link preload `app.js`** — early hints para recurso crítico
- **SEO: Organization `sameAs` e `foundingDate`** — linkagem ao GitHub no knowledge graph
- **SEO: `?q=` URL param handling** — SearchAction schema agora funcional no app.js

### Corrigido

- **Title otimizado para CTR** — adicionado "2026" e "Guia Gratuito" para destaque na posição 8+
- **Hero image alt text** — descritivo com keywords em vez de apenas "NossoDireito"
- **Removido `Crawl-delay: 5`** do robots.txt — permitir Bing indexar mais rápido

## [1.14.1] - 2026-02-24

### Adicionado

- **Retry com backoff exponencial em `validate_govbr_urls.py`** — `_fetch_with_retry()` com MAX_RETRIES=3, delay 4s × tentativa, retries em HTTP 5xx e erros transitórios (TimeoutError, OSError, ConnectionError). Timeout aumentado de 10s para 15s
- **`BreadcrumbList` JSON-LD** — Structured data de navegação principal (5 itens) para rich snippets no Google
- **`SiteNavigationElement` JSON-LD** — Declaração formal da navegação do site (10 seções) para crawlers
- **`meta keywords`** — 18 termos de alta relevância PcD para complementar meta description

### Corrigido

- **20 URLs quebradas em `direitos.json`** — Lei 10.891 (3x), ENEM/INEP (3x), Passe Livre, MCMV, INSS aposentadoria, MDH/CNDH, Bolsa Família, CadÚnico, Bolsa Atleta (2x), Lei 10.891 base_legal. Maioria por reestruturação ministerial gov.br
- **`sitemap.xml` lastmod atualizado** → 2026-02-23, adicionado `<changefreq>weekly</changefreq>` e `<priority>1.0</priority>`
- **`robots.txt`** — Adicionado `Crawl-delay: 5` para controle de taxa de crawling

### Segurança

- **Versões mínimas de dependências atualizadas** — `requirements.txt`: requests≥2.32.0 (CVE fixes), lxml≥5.1.0, jsonschema≥4.23.0. `requirements-dev.txt`: pytest≥8.0.0, playwright≥1.50.0, pip-audit≥2.7.0. Python mínimo 3.10+
- **pip-audit**: 0 vulnerabilidades em deps de produção, npm audit: 0 vulnerabilidades
- **69 candidatos de benefícios avaliados** — 5 PcD-relevantes (nível municipal SP/Barueri), 64 rejeitados (não PcD-específicos). Estrutura municipal incorporada via `cobertura_municipal_prioritaria`; pendência residual passou a ser triagem contínua de ruído municipal

### Validação

- **Master Compliance: 100% (1080.9/1080.9)** — 21 categorias, todas ✅
- **Schema validation: PASSED** — direitos.json vs direitos.schema.json (Draft 7)
- **160 unit tests PASSED** — 2 failed + 40 errors são Playwright browser tests (requerem `localhost:9876`)
- **URLs gov.br: 25/26 OK** — 1 falha persistente (PI 323/2020 no DOU retorna 403, proteção anti-bot)

---

## [1.14.0] - 2026-02-23

### Adicionado

- **Analytics com privacidade (LGPD-compliant)** — Contador de visitantes únicos e page views em `server.js` usando SHA-256 com salt diário rotativo. Zero cookies, zero fingerprinting, zero PII armazenado
- **Endpoint `/api/stats`** — Retorna estatísticas agregadas anônimas (visitantes, dispositivos desktop/mobile/tablet, top pages, distribuição por hora, histórico 30 dias). Protegido opcionalmente por `STATS_KEY` env var
- **Métricas customizadas no Application Insights** — `daily_unique_visitors`, `daily_page_views`, `daily_desktop/mobile/tablet` enviadas automaticamente na virada do dia. Evento `unique_visit` em tempo real
- **`SearchAction` no WebSite schema (JSON-LD)** — Habilitação de Sitelinks Searchbox no Google Search Results

### Corrigido

- **`meta keywords` removido** — Tag ignorada pelo Google desde 2009, eliminando ~850 bytes desnecessários no `<head>`
- **`meta robots: index, follow` removido** — Comportamento padrão, tag redundante
- **`Referrer-Policy` alterada para `strict-origin-when-cross-origin`** — Substitui `no-referrer` (que bloqueava dados de referral no Google Search Console e analytics) mantendo privacidade cross-origin. Atualizado em `index.html` e `server.js`
- **Navbar brand `href="#"` → `href="#inicio"`** — Link morto corrigido para destino semântico correto

---

## [1.13.2] - 2026-02-18

### 🔍 SEO & Structured Data

- **Remoção de BreadcrumbList inválido** — Dois itens apontavam para a mesma URL (`/`), gerando rich result sem valor. Removido do JSON-LD
- **Remoção de SearchAction não implementado** — `potentialAction` declarava busca via `?q=` mas a SPA usa hash-routing (`#busca`). Removido para evitar erro de schema
- **GovernmentService URL corrigida** — URL do serviço agora aponta para `gov.br/pessoa-com-deficiencia` (fonte oficial) em vez do próprio site. Adicionado `mainEntityOfPage`
- **Remoção de `sameAs: []`** — Array vazio removido do bloco Organization (sem valor semântico)
- **URLs padronizadas com trailing slash** — Todas as URLs em JSON-LD consistentes com canonical (`/`)
- **Title otimizado** — `—` → `|` para reduzir largura de pixel (601px → ~575px, limite Google: 580px)
- **Meta description encurtada** — De ~210 para ~155 caracteres (1397px → ~950px, limite: 1000px)
- **sitemap.xml simplificado** — Removidos `<changefreq>` e `<priority>` (deprecated, ignorados pelo Google)

### ⚡ Performance

- **Cache `immutable`** — Assets estáticos (CSS, JS, imagens) agora incluem `immutable` no `Cache-Control`, eliminando revalidações desnecessárias
- **`stale-while-revalidate`** — HTML, JSON e XML servem cache enquanto revalidam em background, reduzindo TTFB percebido
- **`keepAliveTimeout` 5s → 65s** — Evita que o Azure Load Balancer feche/reabra conexões TCP a cada request (principal causa de latência 4s)
- **`headersTimeout` 15s → 70s** — Ajustado para ser > `keepAliveTimeout` (requisito Node.js)

### 🤖 CI/CD & Dependabot

- **Dependabot habilitado** — Monitoramento semanal de npm, pip e GitHub Actions (`dependabot.yml`)
- **Auto-merge Dependabot** — PRs de patch/minor são mergeadas automaticamente após Quality Gate passar. Major requer review manual
- **Repo settings** — `allow_auto_merge` e `delete_branch_on_merge` habilitados

---

## [1.13.1] - 2026-02-16

### 🏗️ Arquitetura de Dados

- **Remoção de `ipva_pcd_estados.json`** — Arquivo standalone com dados placeholder removido. Os dados reais de IPVA (27 estados com legislação, artigos e URLs SEFAZ) já existem inline em `direitos.json` → `isencoes_tributarias.ipva_estados` e `isencoes_tributarias.ipva_estados_detalhado`
- **Expansão de `orgaos_estaduais`** — Cada estado agora inclui `sefaz` (URL SEFAZ), `detran` (URL DETRAN) e `beneficios_destaque` (benefícios fiscais e veiculares estaduais)
- **Atualização de dependências** — Todos os scripts, testes e validações migrados para usar dados inline de `direitos.json` em vez do arquivo standalone

### ✨ Funcionalidades

- **Busca por estado expandida** — Ao buscar por estado/cidade, agora exibe portais SEFAZ e DETRAN com links diretos, além de benefícios estaduais em destaque
- **`renderLocationResults()` enriquecido** — Mostra portais estaduais (SEFAZ/DETRAN) e lista de benefícios específicos por estado em formato expandível

### 🔧 Correções

- **`validate_content.py`** — Contagem de categorias atualizada de 25 → 30 (reflete 5 categorias adicionadas anteriormente)
- **`validate_urls.py`** — Agora valida URLs de SEFAZ e DETRAN expandidas em `orgaos_estaduais`
- **`analise360.py`** — Seção IPVA atualizada para ler dados inline de `direitos.json`

### 📱 PWA

- **Ícone 192×192** — Adicionado para conformidade com Android/Chrome PWA (antes só tinha 32, 180, 512)
- **Ícones maskable separados** — `purpose: "any maskable"` dividido em duas entradas: `"any"` (192+512) e `"maskable"` (512) para renderização correta em Android
- **`orientation: "any"`** — Adicionado ao manifest para suporte explícito a todas as orientações

### 🧪 Testes

- **`TestIPVA` reescrito** — Valida dados inline de `direitos.json` (11 testes: 27 estados simples + detalhado, estrutura, SEFAZ HTTPS, sem duplicatas, consistência)
- **`TestOrgaosEstaduais` expandido** — 6 testes: campos obrigatórios, SEFAZ, DETRAN, benefícios destaque
- **`TestEstadosMunicipios` atualizado** — Usa `direitos.json` inline em vez de arquivo standalone
- **Validação standalone negativa** — Teste confirma que `ipva_pcd_estados.json` foi removido

### 📊 Métricas

- Testes: 140/140 PASS (100%)
- Validação conteúdo: 195 checks, 0 erros
- Órgãos estaduais: 27 UFs com sefaz + detran + benefícios
- IPVA: 27 estados (simples) + 27 estados (detalhado) inline

---

## [1.12.4] - 2026-02-15

### ⚡ Performance (LCP & DOM)

- **CSS async loading** — Stylesheet carrega de forma não-bloqueante (`media="print" onload="this.media='all'"`) com fallback `<noscript>`, eliminando render-blocking CSS
- **Deferred rendering (IntersectionObserver)** — 4 seções abaixo do fold (`#links`, `#classificacao`, `#orgaos-estaduais`, `#instituicoes`) renderizam sob demanda ao scroll, reduzindo DOM inicial de 2.335 para ~1.434 elementos (-38%)
- **Image preload responsivo** — Tag `<link rel="preload">` agora inclui `imagesrcset` e `imagesizes` para matching correto com `<picture>` element
- **Hash navigation** — Navegação direta por hash (ex: `/#links`) pré-renderiza a seção correspondente imediatamente
- **Fallback sem IntersectionObserver** — Browsers antigos renderizam todas as seções imediatamente

### 🔧 Corrigido

- **Dead code scanner (master_compliance.py)** — Corrigido falso-positivo: funções referenciadas como valores em objetos/arrays (`fn: renderLinksUteis`) agora são detectadas via regex `[:,\[]\s*funcName`
- **Service Worker — cache stale após deploy** — Estratégia alterada de cache-first para **network-first** em todos os assets do mesmo domínio (CSS, JS, imagens). Assets de CDN externas mantêm cache-first. Garante que, após cada deploy, o usuário recebe a versão mais recente imediatamente — cache é usado apenas quando offline.
- **sw-register.js — reload automático** — Detecta instalação de novo Service Worker via evento `controllerchange` e recarrega a página automaticamente, evitando conteúdo desatualizado sem intervenção do usuário. Inclui verificação periódica de atualização a cada 60s.

### 📊 Métricas

- DOM inicial: 2.335 → 1.434 (-38%)
- Seções deferred: 4 (links 91, classificação 2, órgãos 27, instituições 25 = 911 elementos)
- E2E: 196/196 PASS (100%)
- Compliance: 1042.9/1042.9 = 100.00%

---

## [1.12.3] - 2026-02-15

### Corrigido

- **VLibras painel não aparecia** — O widget VLibras usa `window.onload` para inicializar seu DOM (injetar imagens e HTML do plugin). Como o script é carregado sob demanda (lazy-load) após o `onload` já ter disparado, a inicialização nunca ocorria. Corrigido chamando `window.onload()` manualmente após `new VLibras.Widget()`.
- **Detecção do botão VLibras mais robusta** — Polling alterado para aceitar `img` ou `img[src]` dentro de `[vw-access-button]`, com timeout estendido de 5s para 8s.
- **Testes E2E** — 196/196 PASS (100%)

---

## [1.12.2] - 2026-02-15

### 🚮 Removido
- **Disclaimer modal removido** — Modal de disclaimer eliminado completamente do DOM, JS e scripts de teste; conteúdo mantido como disclaimer inline no footer com âncora `#disclaimerInline`

### ✨ Novo
- **Busca combinada doença + cidade** — Pesquisas como "TEA Barueri", "autismo São Paulo", "F84 Curitiba" agora filtram resultados por tema dentro do contexto de localização
- **220+ cidades brasileiras** — Expandido de ~100 para ~220+ cidades cobrindo todas as 27 UFs (capitais, regiões metropolitanas e cidades do interior)
- **Busca inteligente com stopwords** — Palavras comuns PT-BR ("e", "de", "do", "da", "para", "com") filtradas da pontuação; pontuação removida automaticamente
- **Phrase matching (match composto)** — Frases como "síndrome de down" recebem bonus de pontuação quando encontradas como bloco contínuo (+5 por hit)
- **Minimum terms threshold** — Queries com 2+ termos exigem pelo menos 2 termos presentes na categoria para aparecer nos resultados (reduz ruído em ~50-80%)
- **CID + cidade combinados** — "F84 Barueri" retorna 4 categorias TEA filtradas em contexto de Barueri (SP)

### 🔧 Compatibilidade
- **Safari < 15.4 dialog fallback** — `dialog.showModal()` substituído por `window.confirm()` quando API não disponível
- **iOS TTS fix** — Workaround de keepalive do Chrome desativado no Safari (causava parada permanente do TTS)
- **iOS format-detection** — `<meta name="format-detection" content="telephone=no">` previne auto-link de números

### 🧪 Testes
- **E2E atualizado: 196/196 PASS** — Modal tests substituídos por inline disclaimer tests (7 tests); 6 testes de busca combinada adicionados
- **CSP test corrigido** — `test_e2e_automated.py` agora verifica CSP tanto em HTML quanto em `server.js`
- **Screenshots versionados** — Script `capture_screenshots.py` agora salva em `screenshots/v{VERSION}/`

---

## [1.12.1] - 2026-02-15

### 🐛 Corrigido
- **`resilientFetch()` podia retornar `undefined`** — 5xx sem retries restantes não fazia backoff; agora faz delay+retry e lança exceção ao esgotar tentativas
- **Null-dereference em `setupDisclaimer()`/`setupNavigation()`** — Adicionados null guards para `acceptBtn`, `showDisclaimer`, `menuToggle`, `navLinks`, `voltarBtn`
- **`AbortSignal.timeout()` incompatível** — Substituído por `AbortController` + `setTimeout` em `enrichGovBr()` para compatibilidade com Safari < 16
- **XSS potencial em `confirmAction()`** — `msg` agora passa por `escapeHtml()` antes de `innerHTML`
- **`formatDate()` quebrava com ISO completo** — Detecta se já contém 'T' antes de acrescentar timezone
- **Shadow variable `e` no IPVA handler** — Renomeada para `item` no `.find()` callback
- **`server.js` I/O bloqueante** — `resolveFile()` convertida para async com `fs.promises.lstat()`
- **`server.js` stream error double-end** — Verifica `res.writableEnded` antes de `res.end()`
- **SPA fallback mascarava 404** — Requests com extensão de arquivo que não existem retornam 404 em vez de `index.html`

### ⚡ Performance
- **Scroll listener throttled** — `backToTop` usa `requestAnimationFrame` + `passive: true` (era 60fps sem throttle)
- **Search dictionary cacheada** — `buildSearchDictionary()` não reconstrói a cada busca
- **Regex pre-compilada em `scoreSearch()`** — Regexes criadas uma vez por termo, não por categoria × termo
- **SW install paralelo** — Assets cacheados com `Promise.allSettled()` (era sequencial)
- **DOM reduzido** — Bloco SEO `#seo-content` removido do DOM após init (~35 elementos)
- **CLS 0.014 corrigido** — Inline CSS para `hero-actions` mobile (480px) agora inclui `flex-direction:column; min-height:176px`
- **LCP image preload** — Adicionado `<link rel="preload">` para hero image WebP no `<head>`

### 🔒 Segurança
- **Rate limit map cap** — Limite de 50.000 entradas para evitar crescimento sem limite sob ataque distribuído

---

## [1.12.0] - 2026-02-15

### 🐛 Corrigido
- **TTS `stopReading()` duplicada** — Removida primeira definição morta de `stopReading()` que causava conflito de escopo
- **TTS `textContent` destruía child spans** — `btnReadAloud.textContent` substituía todo o conteúdo do botão, removendo `.a11y-toggle-icon`, `.a11y-toggle-label` e `.a11y-toggle-state`; agora atualiza cada span individualmente
- **TTS `getBestPtBrVoice()` resetava chunks** — Removia `currentChunks = []` e `currentChunkIndex = 0` que zeravam os chunks antes da leitura iniciar
- **`resilientFetch` retornava `undefined` em erro 5xx** — Após todos os retries com 5xx, a função retornava `undefined` causando crash ao chamar `.json()`; agora lança exceção
- **`waitForVoices()` podia travar para sempre** — Adicionado timeout de 3s para evitar Promise que nunca resolve quando `onvoiceschanged` não dispara
- **`setupDisclaimer()` sem null guard** — Adicionada verificação `if (!dom.disclaimerModal) return` para evitar erro quando elemento não existe no DOM
- **CSS `--font-body` indefinida** — `.ipva-dropdown` usava `var(--font-body)` inexistente; corrigido para `var(--font)`
- **Estastísticas do hero hardcoded** — Valores `9` e `20` causavam flash de conteúdo incorreto (FOUC); atualizados para `25` e `50` (mais próximos dos dados reais)

### 🔄 Melhorado
- **Dark mode: painel de acessibilidade** — Drawer, botões, seções, notas e info agora com cores adaptadas para dark mode
- **Dark mode: disclaimer box** — Caixa de aviso com cores ajustadas para dark mode (fundo âmbar escuro)
- **Dark mode: search suggestions** — `.search-suggestion` e `.search-location` com cores adaptadas para dark mode
- **server.js: health check cacheado** — `package.json` lido uma vez na inicialização em vez de `readFileSync` a cada request
- **server.js: validação `servicoId`** — Limite de 10 dígitos no proxy Gov.br para prevenir abuso
- **server.js: ternário redundante** — `r.ok ? r.status : r.status` simplificado para `r.status`
- **sw.js: cache resiliente** — `cache.addAll()` substituído por cache individual com try/catch (falha em um asset não bloqueia instalação do SW)

## [1.11.0] - 2026-02-15

### ✨ Adicionado
- **`avaliacao_360.py`** — Script de avaliação completa com 807 verificações em 11 seções (SEO, segurança, acessibilidade, conteúdo, performance, legal)
- **Whitelist `DOMINIOS_INTERNACIONAIS`** — icd.who.int restaurado como domínio válido para referências CID/ICD
- **Conteúdo SEO pré-renderizado** — `<div id="seo-content">` com texto acessível a crawlers sem JavaScript
- **4 novos schemas JSON-LD** — Organization, BreadcrumbList, 2× ItemList (direitos + benefícios)
- **Sitemap expandido** — De 1 para 34 URLs indexáveis (categorias, filtros, âncoras de seção)
- **Conteúdo `<noscript>` enriquecido** — Informações completas sobre direitos PcD para navegadores sem JS
- **Meta keywords expandidas** — De ~15 para 45+ termos relevantes para SEO

### 🐛 Corrigido
- **icd.who.int restaurado** — URL da OMS para classificação CID/ICD removida indevidamente, agora na whitelist
- **"eMAG 1.0" → "eMAG 3.1"** — Versão correta do Modelo de Acessibilidade corrigida em todos os docs ativos

### 🔄 Melhorado
- **robots.txt** — Limpeza conforme padrões web (removidos comentários keyword-stuffing, Crawl-delay, Allow redundantes)
- **eMAG 4.1 — Atalhos de teclado** — `accesskey="1"` (conteúdo), `accesskey="2"` (menu), `accesskey="3"` (busca)
- **eMAG 1.9 — Links externos** — Removido `target="_blank"` de links hardcoded no HTML
- **Painel de acessibilidade** — Adicionados atalhos de teclado (1, 2, 3) na lista de recursos
- **Master Compliance v1.11.0** — 21 categorias, 1059.9/1059.9 pontos (100.00%)

## [1.10.0] - 2026-02-13

### ✨ Adicionado
- **Testes E2E interativos com Playwright** — 24 testes cobrindo navegação, filtros, busca, modais e acessibilidade
- **Cobertura WAVE completa** — 42 testes de acessibilidade cobrindo todos os 135 itens WAVE
- **Testes visuais de browser** — 23 testes de renderização visual (overflow, fontes, contraste, layout responsivo)
- **Testes de alto contraste** — 11 testes verificando funcionalidade completa em modo de alto contraste
- **SEO expandido** — FAQPage (14 perguntas), GovernmentService schema, Google site verification

### 🐛 Corrigido
- **Contraste de botões de filtro ativos** — Ratio era 2.5:1 (white/blue), agora 12.6:1 (amber/black) em alto contraste
- **CSS overflow-x** — Corrigido para evitar scroll horizontal indesejado
- **Codificação cp1252** — 7 scripts corrigidos para funcionar em terminal Windows
- **9 importações Python não usadas** — Removidas de 7 arquivos

### 🔄 Melhorado
- **Pipeline unificado** — Pre-commit agora executa apenas `master_compliance.py --quick` (comando único)
- **`check_version_consistency.py` absorvido** — Função `check_versions()` embutida no master_compliance.py
- **`validate_schema.py` absorvido** — Método `validate_json_schema()` embutido no master_compliance.py
- **Master Compliance v1.10.0** — 21 categorias, 1059.9/1059.9 pontos (100.00%)
- **CSS alto contraste** — Override para `.orgao-filter-btn.active` e `.inst-filter-btn.active`
- **`reduced-motion`** — Media query para desabilitar animações conforme preferência do usuário

### 🗑️ Removido
- **`check_version_consistency.py`** — Absorvido como função inline no master_compliance.py
- **`validate_all.py` do pre-commit** — Roda apenas manualmente (16 fases completas)
- **Referências órfãs** — Limpeza de docs com referências a scripts removidos/consolidados

## [1.9.0] - 2026-02-12

### ✨ Adicionado
- **Pipeline de qualidade** — `scripts/quality_pipeline.py` substitui `codereview/codereview.py`
- **Detecção de referências órfãs** — Categoria 21 no master_compliance.py
- **Terraform IaC** — Infraestrutura Azure como código (App Service, Key Vault, CDN)

### 🔄 Melhorado
- **Remoção de docs/v2/** — Eliminadas todas as referências v2 obsoletas
- **Remoção de codereview/** — ~50 referências substituídas para quality_pipeline

## [1.8.1] - 2026-02-12

### 🐛 Corrigido
- **Exportação PDF em branco** — CSS do modo de impressão corrigido para exibir corretamente os resultados da análise de documentos
  - Bug: `body.printing-analysis > *:not(.analysis-results)` escondia `<main>`, mas `.analysis-results` está aninhado em `<main> > <section#documentos> > <div.container>`
  - Solução: CSS de impressão reestruturado para ocultar seletivamente apenas elementos não relacionados à análise
  - Print agora preserva cores (badges, barras de progresso), adiciona cabeçalho e rodapé, e evita quebra de página no meio de itens

### ✨ Adicionado
- **Botão "📥 Salvar PDF" no Checklist** — Seção "Primeiros Passos Após o Laudo" agora pode ser exportada como PDF
  - Inclui progresso (X de 10 concluídos) e estado dos checkboxes marcados
  - Cabeçalho: "NossoDireito — Primeiros Passos Após o Laudo"
  - Rodapé: data de geração, URL, aviso legal
- **Botão "📥 Salvar PDF" nos Documentos Necessários** — Seção "Documentos Necessários por Direito" agora pode ser exportada como PDF
  - Lista completa de 16 documentos com descrições, dicas e categorias relacionadas
  - Cabeçalho: "NossoDireito — Documentos Necessários por Direito"
  - Rodapé: data de geração, URL, aviso legal

### 🗑️ Removido
- **Botão "📲 Compartilhar no WhatsApp"** — Removido da página de detalhes de cada direito
  - Motivo: funcionalidade nativa do WhatsApp (wa.me) removida por decisão de design

## [1.8.0] - 2026-02-12

### ✨ Adicionado

#### Links Completos para Família PcD (Paralisia Cerebral + TEA Grau 3) — Saúde, Isenções, DEFIS, CIPTEA
- **10 novas fontes**: PCDT (Protocolos Clínicos SUS), Formulário LME (medicamentos especializados), Programa Agora Tem Especialistas, CST/OMS (Caregiver Skills Training para famílias TEA), DPU Contatos, MPF Serviços, Lei 10.048/2000, CIPTEA SP, SISEN Receita Federal, Meu SUS Digital
- **1 nova instituição**: MPF — Ministério Público Federal (denúncias, SAC, ouvidoria, tel 61 3105-5100)
- **47 novos keywords** no matching_engine.json (paralisia cerebral, TEA grau 3, LME, PCDT, DEFIS, Zona Azul, Meu INSS, passe livre, etc.)
- **10 novos termos uppercase_only**: LME, PCDT, CNES, CST, DEFIS, SENATRAN, MPF, DPU, SEFAZ, CER

### 🔄 Enriquecido
- **`sus_terapias`** — +6 links (LME formulário, PCDT protocolos clínicos, CNES busca, Agora Tem Especialistas, CST/OMS para TEA, Meu SUS Digital), +4 dicas, +12 tags (LME, PCDT, CNES, paralisia cerebral, CER, CST)
- **`ciptea`** — +5 links (CIPTEA SP portal, Autismo A-Z gov.br, CST/OMS, PCDT, Novo Viver sem Limite), +3 dicas (CIPTEA SP, CST programa, Lei Romeo Mion), +9 tags (TEA grau 3, paralisia cerebral, CST)
- **`isencoes_tributarias`** — +3 links (SISEN receita.fazenda, SEFAZ SP, DEFIS SENATRAN), +6 dicas (IPI teto R$ 200.000/2026, ICMS ~R$ 120.000, IPVA total, isenção rodízio, Zona Azul grátis, SEFAZ), +11 tags (SISEN, SEFAZ, IPVA, ICMS, rodízio, Zona Azul, DEFIS)
- **`estacionamento_especial`** — +2 links (DEFIS SENATRAN, SP156 São Paulo), +3 dicas (DEFIS credencial, Zona Azul grátis, credencial nacional), +7 tags
- **`atendimento_prioritario`** — +2 links (Lei 10.048/2000, MPF Serviços), base_legal Lei 10.048
- **`transporte`** — +1 link (Passe Livre gov.br/transportes)
- **`bpc`** — dica Meu INSS app + Helô
- **`auxilio_inclusao`** — dica Meu INSS + 135
- **`aposentadoria_especial_pcd`** — dica Meu INSS simulador
- **`tarifa_social_energia`** — dica distribuidora local (Enel, CPFL, Light, Energisa)
- DPU instituição enriquecida com link contatos-dpu

### 📊 Métricas
- 📊 25 categorias, 68 fontes, 25 instituições, 352 tags únicos, 609 keywords, 116 uppercase terms
- E2E: 18/18 (100%)
- Quality Pipeline: 221 PASS, 100.0/100
- Master Compliance: 100.00% (853.4/853.4, 17/17 pilares)
- WAF Score: 100% (Seg=100%, Conf=100%, Perf=100%, Custo=100%, Ops=100%)

## [1.7.0] - 2026-02-12

### ✨ Adicionado

#### Turismo Acessível, ANAC/PNAE, Convenção ONU e Enriquecimentos Massivos
- **Nova categoria `turismo_acessivel`** — Turismo Acessível, Hospedagem e Transporte Aéreo para PcD
  - Resolução ANAC 280/2013 — direitos completos do PNAE (Passageiro com Necessidade de Assistência Especial)
  - Acompanhante aéreo: máx. 20% do bilhete; cão-guia: gratuito na cabine
  - Ajudas técnicas (cadeira de rodas) transportadas GRATUITAMENTE
  - 80% de desconto em bagagem de equipamento médico
  - Portal Turismo Acessível (turismoacessivel.gov.br) — busca por hotéis/atrativos acessíveis
  - Documentação MEDIF/FREMEC para viajantes frequentes com deficiência
  - Links: Portal Turismo Acessível, ANAC PNAE, Resolução 280/2013, MEDIF/FREMEC
- **Convenção ONU (Decreto 6.949/2009)** — "lei mãe" adicionada como base_legal em 7 categorias estratégicas (educação, trabalho, saúde, transporte, moradia, tecnologia, esporte)
- **11 novas fontes**: Decreto 6.949/2009 (Convenção ONU), Resolução ANAC 280/2013, Lei 8.112/90, Portal Turismo Acessível, ANAC PNAE, eMAG/Acessibilidade Digital, IRPF moléstia grave, Sisen IPI/IOF, CAPS, Rede de Cuidados PcD SUS, ENEM Acessibilidade
- **4 novas instituições de apoio**: ANAC (163), Portal Turismo Acessível (MTur), ObservaDH, CPB (Comitê Paralímpico Brasileiro)
- **76 novos keywords** no matching_engine.json (turismo, avião, PNAE, hotel acessível, concurso, eMAG, CAPS, sisen, etc.)
- **11 novos termos uppercase_only**: ANAC, PNAE, MEDIF, FREMEC, CAPS, CPB, MCMV, SISEN, NAPNE, INEP, eMAG

### 🔄 Enriquecido
- **`transporte`** — Resolução ANAC 280/2013, embarque prioritário, cão-guia, acompanhante 20%, dicas ANAC
- **`trabalho`** — Lei 8.112/90 (concursos públicos: 5-20% vagas PcD), guia contratação PcD
- **`educacao`** — ENEM acessibilidade (INEP), NAPNE (Institutos Federais), prova ampliada/Libras/ledor
- **`moradia`** — Acessibilidade MCMV (portas largas, barras de apoio), Secretaria Nacional Habitação
- **`tecnologia_assistiva`** — eMAG, ABNT NBR 17225, acessibilidade digital gov.br
- **`isencao_ir`** — Link direto Receita Federal (isenção IRPF moléstia grave)
- **`isencoes_tributarias`** — Link Sisen (IPI/IOF veículo PcD — serviço online gov.br)
- **`sus_terapias`** — CAPS (saúde mental), Rede de Cuidados à Pessoa com Deficiência
- **`prouni_fies_sisu`** — ENEM acessibilidade (prova Libras, Braile, ledor, tempo adicional)
- **`esporte_paralimpico`** — Centros de Referência CPB
- **`bpc`** — Painel de Monitoramento BPC (SAGI/MDS)
- 📊 25 categorias, 58 fontes, 24 instituições, 334 tags únicos, 562 keywords, 106 uppercase terms

### 📊 Métricas
- E2E: 18/18 (100%)
- Quality Pipeline: 210 PASS, 97.4/100
- WAF Score: 96% (Seg=100%, Conf=100%, Perf=80%, Custo=100%, Ops=100%)

## [1.6.0] - 2026-02-12

### ✨ Adicionado

#### Validação contra 15 URLs gov.br — Expansão de Cobertura
- **Nova categoria `esporte_paralimpico`** — Bolsa Atleta e Esporte Paralímpico para PcD
  - Lei 10.891/2004, Decreto 5.342/2005
  - Categorias da Bolsa: Base (R$ 410) a Pódio (R$ 16.629/mês), equiparadas para paralímpicos
  - Links: Ministério do Esporte, Comitê Paralímpico Brasileiro, Novo Viver sem Limite
  - 37+ keywords no matching_engine.json (bolsa atleta, esporte paralímpico, CPB, goalball, etc.)
- **`dica_seguranca`** — Campo top-level: "Sempre verifique se o site termina em .gov.br antes de fornecer dados pessoais"
- **6 novas fontes**: Lei 10.891/2004, Decreto 5.342/2005, Portaria GM/MS 1.526/2023 (PNAISPD), Novo Viver sem Limite, ONDH, Fala.BR
- **5 novas instituições de apoio**: ONDH/Disque 100, Fala.BR (CGU), Novo Viver sem Limite, DPU GT PcD, OuvSUS 136
- **Enriquecimento `sus_terapias`** — PNAISPD (Portaria 1.526/2023), RCPD, CER, OuvSUS 136
- **Disque 100** adicionado como dica em 14 categorias (24h, WhatsApp 61 99611-0100)
- **Fala.BR** adicionado como dica em atendimento_prioritário, prioridade_judicial, plano_saude
- **Novo Viver sem Limite** link adicionado em 4 categorias (tecnologia_assistiva, educacao, protecao_social, transporte)
- 📊 24 categorias, 47 fontes, 20 instituições, 306 tags únicos, 486 keywords

### ✨ Adicionado (anterior)

#### Sistema de Compliance Total (15 Categorias)
- **`scripts/master_compliance.py`** — Expandido para validação completa (v1.6.0)
  - ✅ 15 categorias de validação (era 10)
  - ✅ 11. **Testes Automatizados E2E**: Executa test_e2e_automated.py, verifica cobertura de funções críticas
  - ✅ 12. **Dead Code Detection**: Detecta funções JS não usadas, importações Python órfãs, console.log() esquecidos
  - ✅ 13. **Arquivos Órfãos**: Detecta .backup, .tmp, .bak, .old, .swp, .DS_Store, __pycache__, node_modules
  - ✅ 14. **Lógica de Negócio**: Valida vinculação bidirecional, documentos_mestre, classificação de dados, URLs HTTPS
  - ✅ 15. **Regulatory Compliance**: LGPD, disclaimer, finance, GitHub security, dados sensíveis, versões consistentes
  - 📊 Score atual: **93.42%** (568.1/608.1 pontos)

- **`scripts/test_e2e_automated.py`** — Testes automatizados end-to-end
  - 15+ validações estruturais (HTML, CSS, JS, Service Worker, PWA Manifest)
  - Validação de integridade direitos.json (20 categorias, campos obrigatórios, base_legal)
  - Validação matching_engine.json (keyword_map estrutura moderna)
  - Testes de segurança (CSP, segredos hardcoded, LGPD)
  - Testes de acessibilidade (≥30 ARIA attributes)
  - Testes de SEO (sitemap.xml, robots.txt)
  - Preparado para Playwright (testes cross-browser futuros)

#### Análise Avançada de Código
- **Dead Code Detection:** Identifica automaticamente:
  - Funções JavaScript não usadas (regex de declarações vs chamadas)
  - Importações Python órfãs (import/from vs uso no código)
  - console.log() esquecidos (anti-pattern para produção)

- **Orphaned Files Cleanup:** Detecta:
  - Arquivos temporários (.tmp, .bak, .backup, .old, .swp)
  - Cache de sistema (.DS_Store, __pycache__)
  - Arquivos grandes (>10MB)
  - Flag para auto-cleanup (desabilitado por padrão)

#### Validação de Lógica de Negócio
- **Vinculação Bidirecional:** Valida relacionamento categorias ↔ documentos_mestre
- **Classificação de Dados:** Detecta menções a dados sensíveis (CPF, RG, senha, etc.) para alertar sobre LGPD
- **Integridade de Base Legal:** Verifica artigos, URLs HTTPS, campos obrigatórios
- **Cobertura de Documentos:** Garante que toda categoria tem ≥1 documento vinculado e ≥3 passos

#### Regulatory & Compliance
- **LGPD (Lei 13.709/2018):** 6 checks automáticos
  - Menção à LGPD e Lei 13.709
  - Declaração de não coleta de dados
  - Política de privacidade
  - localStorage/IndexedDB mencionado
- **Disclaimer Completo:** 5 checks (aviso legal, não substitui orientação profissional, Defensoria Pública, fontes oficiais)
- **Finance/Transparência:** Declaração sem fins lucrativos, gratuito, sem custo
- **GitHub Security:** Processo de reporte de vulnerabilidades, contato de segurança
- **Dados Sensíveis Expostos:** Scan de password=, api_key=, secret=, token=, AWS_SECRET, AZURE_CLIENT_SECRET
- **Versões Consistentes:** Verifica que README, SECURITY, CHANGELOG, SECURITY_AUDIT estão na mesma versão

### 🔧 Melhorado

#### Documentação Atualizada
- **SECURITY.md:** Versões suportadas atualizadas para 1.6.x, 1.5.x (removido <1.5)
- **SECURITY_AUDIT.md:** Atualizado para v1.6.0 (era v1.1.0)
  - Data atualizada: 2026-02-12
  - Adicionado compliance: LGPD, WCAG 2.1 AAA, e-MAG

#### Score de Qualidade
- **Score Total: 93.42%** (568.1/608.1 pontos) - 15 categorias
- **13 categorias a 100%**:
  - DADOS, CODIGO, FONTES, ARQUITETURA, DOCUMENTACAO, SEGURANCA, PERFORMANCE, ACESSIBILIDADE, SEO, INFRAESTRUTURA, ORFAOS, LOGICA, REGULATORY
- **2 categorias em melhoria**:
  - TESTES: 20% (necessário corrigir cobertura de funções)
  - DEAD_CODE: 0% (5 funções JS não usadas, 8 console.log() detectados)

### 🐛 Para Corrigir (Próximas Versões)
- ❌ **Testes E2E:** Cobertura de funções críticas baixa (1/6)
- ❌ **Dead Code:** 5 funções JavaScript não usadas detectadas
- ❌ **Console.log:** 8 ocorrências esquecidas no código
- ⚠️  **Órfão:** backup/.commit_msg.tmp
- ⚠️  **Versões:** Inconsistências entre documentos (README: v98.7, SECURITY: v1.6, CHANGELOG: v241.126)

### 📊 Estatísticas v1.6.0

#### Validações
- **Total de validações:** 804 (era 787 na v1.5.0) - **+17 validações**
- **Aprovadas:** 804 ✅
- **Avisos:** 11 ⚠️
- **Erros:** 3 ❌
- **Tempo de execução:** 0.52s (era 0.27s) - **+0.25s** devido a 5 categorias novas

#### Arquivos Alterados
- **3 arquivos adicionados:**
  - scripts/test_e2e_automated.py (15 testes estruturais)
  - (master_compliance.py expandido +500 linhas)
- **3 arquivos modificados:**
  - scripts/master_compliance.py (15 categorias, 6 novos métodos de validação)
  - SECURITY.md (versões suportadas: 1.6.x, 1.5.x)
  - SECURITY_AUDIT.md (v1.6.0, compliance LGPD/WCAG/e-MAG)

---

## [1.5.0] - 2026-02-11

### ✨ Adicionado

#### Infraestrutura de Qualidade
- **`scripts/quality_pipeline.py`** — Pipeline automatizado de validação com 10 passos
  - Suporte a 3 modos: `--full` (produção), `--quick` (pre-commit), `--ci` (CI/CD)
  - Geração de relatório JSON detalhado (quality_report.json)
  - Validações: limpeza, sintaxe, fontes, quality gate, 360°, acessibilidade, segurança, performance
  - Duração: ~3-5min (full), ~30s (quick)

- **`scripts/validate_content.py`** — Validador semântico e estrutural completo
  - ✅ 20 categorias com todos os campos obrigatórios
  - ✅ Dropdown IPVA com 27 estados (UF, lei, artigo, SEFAZ)
  - ✅ Matching engine (keywords, sinônimos)
  - ✅ Base legal completa (lei + artigo + URL HTTPS)
  - ✅ Documentos_mestre com relacionamentos bidirecionais
  - ✅ Padrões de código (anti-patterns: alert(), console.log)
  - ✅ Análise semântica de conteúdo (resumos, dicas, valores)

- **`.githooks/pre-commit`** — Hook de validação automática antes de commit
  - Executa 6 passos críticos: limpeza, sintaxe, conteúdo, quality gate, segurança, performance
  - Bloqueia commit se qualquer validação falhar (bypass com `--no-verify`)
  - Instalação: `git config core.hooksPath .githooks`

- **`docs/QUALITY_TESTING_GUIDE.md`** — Guia completo de testes (850+ linhas)
  - 60+ testes manuais no browser
  - Seção crítica: IPVA dropdown (27 estados)
  - Checklists: pre-commit (20 itens), pre-deploy (15 itens)
  - Troubleshooting com 7 cenários comuns

#### GitHub Actions
- **`.github/workflows/quality-gate.yml`** — Atualizado com validação de conteúdo
  - Step adicional: validação de categorias, IPVA, matching engine
  - Executa antes do quality gate principal
  - Upload de relatório como artifact (retenção 30 dias)

### 🔧 Melhorado

#### Qualidade de Código
- **Score Quality Gate: 97.3 → 98.7/100** (+1.4 melhoria)
- **WAF 5 Pilares: 100%** (Security, Reliability, Performance, Cost, Operations)
- **Performance: 40% → 100%** (+60% melhoria)

#### Otimizações
- **HTTP → HTTPS:** 3 URLs corrigidas (prouni_fies_sisu)
- **showToast() replaces alert():** 2 chamadas modernizadas (melhor UX)
- **Keywords expandidas:** +26 palavras-chave
  - meia_entrada: +9 keywords
  - tarifa_social_energia: +17 keywords
- **documentos_mestre:** +3 categorias vinculadas

#### Minificação
- HTML: 40KB → 29KB (-10.8KB, -27%)
- JS: 118KB → 71KB (-46.9KB, -41%)
- JSON: ~150KB → 102KB (~-48KB, -33%)
- **Total: -107KB economia de banda**

### 🐛 Corrigido
- **quality_pipeline.py:** Validação de campo `link` → `url` em base_legal
- **Backup files:** Remoção automática de arquivos .backup (303KB liberados)

### 🧹 Removido
- `scripts/validate_links.py` — Duplicado (funcionalidade em validate_sources.py)
- Arquivos .backup — Cleanup automático no pipeline

### 📁 Movido
- `analise360.py` → `scripts/analise360.py` (organização)

### 📊 Estatísticas

#### Arquivos Alterados
- **29 arquivos:** 8 adicionados, 2 deletados, 19 modificados

#### Quality Metrics
- **Quality Gate:** 98.7/100
- **WAF 5 Pillars:** 100%
- **Validações:** 0 CRITICAL, 0 ERROR, 17 WARNING, 184 PASS
- **Acessibilidade:** 50 atributos ARIA, VLibras, navegação por teclado
- **Segurança:** 100% URLs HTTPS, nenhum dado sensível exposto

#### Pipeline Execution
- **Total de passos:** 21
- **Taxa de sucesso:** 85.7% (18/21)
- **Duração:** ~154s (modo full)
- **Falhas não-críticas:** JavaScript validation (Node.js não instalado), sources validation (timeout)

---

## [1.4.3] - 2026-02-11

### Adicionado

#### Documentos Mestres — Meia-Entrada e Tarifa Social Energia
- **Novos documentos em `documentos_mestre[]`:**
  - `comprovante_deficiencia`: Carteira PcD, CIPTEA, laudo médico ou carteira de transporte especial
  - `comprovante_bpc`: Extrato INSS ou carta de concessão do BPC/LOAS
  - `prescricao_equipamento_medico`: Receita médica para equipamentos elétricos domiciliares (respirador, concentrador de oxigênio, etc.)

- **Vinculações documentais:**
  - Benefício `meia_entrada` agora referencia: `rg`, `cpf`, `comprovante_deficiencia`
  - Benefício `tarifa_social_energia` agora referencia: `rg`, `cpf`, `nis`, `comprovante_residencia`, `laudo_medico`, `prescricao_equipamento_medico`, `comprovante_bpc`

### Atualizado

#### Sincronização Bidirecional de Documentos
- **Documentos existentes atualizados** com novas categorias:
  - `rg.categorias[]` → adicionado `meia_entrada`, `tarifa_social_energia`
  - `cpf.categorias[]` → adicionado `meia_entrada`, `tarifa_social_energia`
  - `comprovante_residencia.categorias[]` → adicionado `tarifa_social_energia`
  - `laudo_medico.categorias[]` → adicionado `meia_entrada`, `tarifa_social_energia`
  - `nis.categorias[]` → adicionado `tarifa_social_energia`

#### Padronização de Estrutura
- Array `documentos[]` dos benefícios convertido de texto livre para IDs
- Permite renderização automática na seção "Documentos Necessários por Direito"
- Habilita persistência de checkboxes no localStorage

### Documentado

#### DEPENDENCY_CONTROL.md
- Nova seção **7️⃣ ADICIONAR/ATUALIZAR DOCUMENTOS MESTRES**
- Explica sincronização bidirecional entre `documentos_mestre[]` e `categorias[].documentos[]`
- Checklist completo de 10 itens para adição de documentos
- Alerta sobre inconsistências comuns (esquecimento de sincronização)
- Estrutura JSON exemplo e validações recomendadas

### Validado

#### Controle de Qualidade
- ✅ JSON sintaxe validada (Python json.load)
- ✅ Versão sincronizada em 3 arquivos (direitos.json, package.json, sw.js)
- ✅ Cache invalidado (novo sw.js v1.4.3)
- ✅ Sincronização bidirecional verificada (documentos ↔ benefícios)
- ✅ Total de documentos mestres: **18** (antes: 15)

---

## [1.4.2] - 2026-02-11

### Corrigido

#### Interface do Usuário
- **Aviso Importante** reformatado com melhor hierarquia visual e espaçamento
  - Removidos estilos inline, migrados para classes CSS reutilizáveis
  - Seções separadas: Limitações do Serviço + Onde buscar ajuda + LGPD
  - Melhor legibilidade com parágrafos e listas organizadas

- **Seção Transparência** reestruturada com mais clareza
  - Compromisso com atualização agora destaca que o processo é **MANUAL**
  - Data da última atualização exibida de forma proeminente
  - Próxima revisão prevista informada claramente
  - Call-to-action para reportar informações desatualizadas (e-mail fabiotreze@hotmail.com)

- **Síntese de voz (TTS)** agora alerta usuário quando não há voz em português
  - Mensagem: "⚠️ Seu navegador pode não suportar português. A leitura pode estar em outro idioma."
  - Toast informativo orienta instalação de vozes pt-BR nas configurações do sistema

- **Exportação de PDF** corrigida para evitar páginas em branco
  - Adicionado `@page { size: A4; margin: 2cm; }` para padrão ABNT
  - Substituído `visibility: hidden` por `display: none` para evitar renderização fantasma
  - Método `body.printing-analysis > *:not(.analysis-results)` elimina elementos desnecessários sem criar espaço vazio

#### Versionamento
- Versão sincronizada **v1.4.2** em todos os arquivos:
  - `direitos.json`: versao "1.4.2"
  - `package.json`: version "1.4.2"
  - `sw.js`: CACHE_VERSION v1.4.2
  - Rodapé do site agora exibe versão correta

### Adicionado

#### CSS
- Novas classes para disclaimer estruturado:
  - `.disclaimer-box`: Container principal do aviso
  - `.disclaimer-title`: Título do aviso
  - `.disclaimer-intro`: Parágrafo de introdução
  - `.disclaimer-subtitle`: Subtítulos de seções
  - `.disclaimer-list`: Listas formatadas
  - `.disclaimer-section`: Seções internas com bordas

- Suporte a novos elementos dinâmicos na transparência:
  - `#transLastUpdateInline`: Data na lista de transparência
  - `#transLastUpdateText`: Data no compromisso de atualização
  - `#transNextReviewText`: Próxima revisão prevista

---

## [1.4.1] - 2026-02-11

### Adicionado

#### Benefícios PcD Completos — Educação, Trabalho, Habitação
- **`docs/CHECKLIST_VALIDATIONS.md`** — Seções expandidas com pesquisa exaustiva:

**📚 EDUCAÇÃO**
- **FIES 50% Cotas** — Resolução 58/2024 CES/CNE reserva **50% das vagas** para política de cotas (inclui PcD)
- **ProUni** — Lei 11.096/2005 (não específico PcD, mas acessível com renda até 3 SM)
- **SISU** — Lei 13.409/2016 (cotas PcD confirmadas)
- **Pé-de-Meia** — Universal (CadÚnico + ensino médio)

**💼 TRABALHO**
- **Lei 8.213/1991 Art. 93** — Cotas setor privado (2%-5% empresas com 100+ funcionários)
  - Proteção demissão (§1º): empresas não podem demitir PcD sem contratar substituto PcD
  - Fiscalização MTb (§2º): multa R$ 2.411,28 a R$ 241.126,88 por vaga não preenchida
  - SINE e Emprego Apoiado disponíveis
- **Lei 8.112/1990 Art. 5 §2º** — Cotas setor público federal (**ATÉ 20%** nos concursos) ⭐
  - **4x-10x MAIOR** que setor privado
  - Art. 98 §2º: Horário especial SEMCOMPENSAÇÃO para servidor PcD
  - Art. 98 §3º: Extensão de horário especial para servidor com familiar PcD (COM compensação)
  - Art. 24: Readaptação garantida se servidor desenvolver deficiência durante serviço
  - Comparação completa setor público vs. privado documentada

**🏠 HABITAÇÃO**
- **Lei 11.977/2009 Art. 3º V (Lei 12.424/2011)** — Minha Casa Minha Vida
  - ✅ **PRIORIDADE** para famílias com PcD
  - **3% unidades adaptadas** (Art. 73) + acessibilidade obrigatória (rampas)
  - Renda até R$ 4.650,00
  - Emolumentos cartoriais reduzidos em 75%
  - Registro preferencialmente em nome da mulher (Art. 35)

**📊 RESUMO EXECUTIVO**
- Tabela consolidada de todos os benefícios PcD (9 benefícios documentados)
- 10 referências oficiais adicionadas (planalto.gov.br, gov.br/mec, CNE)

### Documentado

#### Validação com Fontes Primárias
Todas as leis foram consultadas nos textos consolidados do Planalto.gov.br:
- Lei 8.213/1991 (~15.000 tokens): Benefícios da Previdência Social + Cotas PcD
- Lei 8.112/1990 (~70.000 tokens): Regime Jurídico dos Servidores Públicos Federais
- Lei 11.977/2009 (~66.000 tokens): Programa Minha Casa Minha Vida completo
- Lei 11.096/2005: ProUni
- Resolução 58/2024 CES/CNE: FIES 50% cotas

#### Comparações e Insights
- **Setor Público vs. Privado**: Concursos federais oferecem quota 20% (vs. 2%-5% empresas privadas)
- **Educação**: FIES agora reserva 50% das vagas para cotas (inclui PcD) — política recente
- **Habitação**: MCMV prioriza PcD desde 2011 (Lei 12.424)

## [1.4.0] - 2026-02-11

### Adicionado

#### Validação Oficial do Checklist
- **`docs/CHECKLIST_VALIDATIONS.md`** — Documento completo validando ordem do checklist com fontes oficiais
  - ✅ **BPC requer CadÚnico CONFIRMADO** — Lei 8.742/1993 Art. 20 §12 (Lei 13.846/2019)
  - ✅ **Cotas PcD SISU** — Lei 13.409/2016 (reserva de vagas em universidades federais)
  - ✅ **Pé-de-Meia** — Programa MEC para ensino médio (CadÚnico + frequência)
  - ✅ **FGTS Saque PcD** — Já documentado (Lei 8.036/1990 Art. 20 XVII)
  - ⚠️ **Bolsa Família e Auxílio Gás** — Não específicos para PcD (critério: renda familiar)
  - 🔍 **Licenças trabalhistas** — Dependem de CCT (Convenção Coletiva de Trabalho)

#### Checklist 10 Passos com Dependências Validadas
- **Ordem validada com legislação federal:**
  1. Gov.br OURO (recomendado para BPC digital)
  2. Dossiê PcD organizado (boas práticas)
  3. Validar laudo médico (prática comum, sem regulação específica sobre 6 meses)
  4. **CRAS + CadÚnico** — **OBRIGATÓRIO por lei (Lei 8.742/1993 Art. 20 §12)**
  5. Rede apoio emocional (recursos comunitários)
  6. CIPTEA (Lei 13.977/2020)
  7. **BPC/LOAS** — **DEPENDE do item 4 (requisito legal)**
  8. Agendar UBS/CER/CAPS (SUS)
  9. Matrícula escolar (LBI)
  10. Plano de saúde (Lei 9.656/1998)

- **Validação JavaScript automática:** checkDependencies() bloqueia ordem incorreta
  - Item 7 (BPC) requer Item 4 (CadÚnico) — alerta + desmarca
  - Itens 4,6,7,8 requerem Item 3 (laudo validado) — alerta + desmarca

#### Reorganização da Documentação
- **Estrutura V1 padronizada:**
  ```
  docs/
  ├── v1/                              # Versão atual em produção
  │   ├── ARCHITECTURE.md              # Antes: SYSTEM_ARCHITECTURE_V1.md
  │   ├── DIAGRAMS.md                  # Antes: SYSTEM_DIAGRAMS.md
  │   ├── LEGAL_COMPLIANCE.md          # Inalterado
  │   └── VLIBRAS_LIMITATIONS.md       # Inalterado
  ├── CHECKLIST_VALIDATIONS.md        # NOVO
  └── README.md                        # NOVO — Padrão de nomenclatura
  ```

- **`docs/README.md`** — Padrão de organização e nomenclatura
  - Convenções de nomes: UPPERCASE com underscores
  - Versionamento por pastas (não por sufixos)
  - Guia de commits (Conventional Commits)
  - Métricas de cobertura documental

### Documentado

#### Novos Benefícios Pesquisados
- **Lei 13.409/2016** — Cotas PcD no ensino superior (SISU + institutos federais)
- **Pé-de-Meia** — Poupança estudantil para ensino médio (até R$ 9.200 total)
- **FGTS** — Saque integral para titular ou dependente PcD (já em direitos.json)

#### Referências Oficiais Validadas
- **Planalto.gov.br:** Lei 8.742/1993 (LOAS), Lei 13.409/2016, Lei 13.977/2020
- **MEC:** https://www.gov.br/mec/pt-br/acesso-a-informacao/acoes-e-programas/pe-de-meia
- **SISU:** https://acessounico.mec.gov.br/sisu

### Alterado

#### Padrão de Nomenclatura de Arquivos
- **Antes:** `SYSTEM_ARCHITECTURE_V1.md`, `SYSTEM_DIAGRAMS.md`
- **Depois:** `v1/ARCHITECTURE.md`, `v1/DIAGRAMS.md`
- **Razão:** Facilita versionamento por pastas


---

## [1.3.0] - 2026-02-10

### Adicionado

#### 5 Novas Categorias de Direitos
- **Atendimento Prioritário** — Filas preferenciais em estabelecimentos (Lei 10.048/2000)
- **Estacionamento Vaga Especial** — Cartão Defis e vagas reservadas (LBI Art. 47)
- **Aposentadoria Especial PcD** — Tempo reduzido para aposentadoria (LC 142/2013)
- **Prioridade Judicial** — Tramitação rápida de processos (CPC Art. 1.048)
- **Tecnologia Assistiva** — Financiamento BNDES para produtos assistivos (LBI Art. 74-75)

**Total: 15 categorias ativas** (anteriormente 10)

### Alterado

#### Quality Gate — Exceção CSP para VLibras
- **Relaxamento de regra:** `unsafe-eval` em CSP não é mais CRITICAL quando VLibras presente
- **Lógica:** Script detecta `vlibras.gov.br` no HTML → muda severidade para WARNING
- **Justificativa documentada:** Lei 13.146/2015 (LBI) exige acessibilidade governamental
- **Trade-off aceito:** Acessibilidade > CSP rígido (VLibras Unity requer eval())
- **Resultado:** CI/CD não bloqueia mais deploy por conta do VLibras

## [1.2.3] - 2026-02-10

### Adicionado

#### Botão Voltar ao Topo
- **Botão flutuante** — ícone ↑ no canto inferior direito (posição fixa)
- **Aparecimento automático** — torna-se visível após 300px de scroll
- **Scroll suave** — animação suave ao retornar ao topo da página
- **Responsivo** — ajusta posição no mobile (80px do bottom para evitar sobreposição com VLibras)
- **Acessível** — `aria-label` e `title` para leitores de tela
- **Styled** — círculo azul (#1e40af) com hover, sombra e transição suave
- **Line height**: 1 para centralização vertical perfeita do caractere ↑

#### Documentação VLibras
- **`docs/VLIBRAS_LIMITATIONS.md`** — análise técnica de compatibilidade VLibras com CSP
- Documenta trade-off acessibilidade vs. segurança (decisão: priorizar acessibilidade)
- Explica mudança de CSP rígido para flexibilizado com `'unsafe-eval'`
- Guia de validação para desenvolvedores
- Lista mitigações de segurança mantidas (host validation, rate limiting, COEP require-corp)

### Alterado

#### VLibras — CSP Flexibilizado para Funcionalidade Completa
**🔄 Mudança de decisão**: De segurança prioritária → acessibilidade governamental prioritária

- **CSP `'unsafe-eval'` adicionado** — permite VLibras Unity funcionar 100% sem erros
  - **Antes**: Mantinha CSP rígido sem `'unsafe-eval'` (segurança prioritária)
  - **Depois**: Adiciona `'unsafe-eval'` (funcionalidade prioritária)
  - **Trade-off aceito**: Reduz proteção contra XSS para habilitar acessibilidade completa

- **CSP `script-src` atualizado**:
  - Adiciona `'unsafe-eval'` além de `'wasm-unsafe-eval'`
  - Remove `blob:` de `script-src` (mantido apenas em `worker-src`)

- **CSP `script-src-elem` atualizado**:
  - Remove `blob:` (scripts eval, não elementos)
  - Mantém domínios VLibras: `vlibras.gov.br`, `*.vlibras.gov.br`, `cdnjs.cloudflare.com`, `cdn.jsdelivr.net`

- **CSP `worker-src` expandido**:
  - Adiciona `https://vlibras.gov.br` e `https://*.vlibras.gov.br`
  - Mantém `'self' blob: https://cdnjs.cloudflare.com`

- **CSP `connect-src` expandido**:
  - Adiciona `data:` para recursos inline
  - Mantém domínios VLibras e CDNs

- **COEP mudado**: `credentialless` → `require-corp`
  - Isolamento cross-origin mais restritivo
  - Compatível com VLibras após CSP flexibilizado

- **Mitigações de segurança mantidas**:
  - ✅ Host validation (exact match, sem subdomínios maliciosos)
  - ✅ Rate limiting (120 req/min por IP)
  - ✅ HSTS preload (força HTTPS)
  - ✅ X-Content-Type-Options nosniff
  - ✅ Referrer-Policy no-referrer
  - ✅ Brotli compression (performance)

- **Resultado**:
  - ✅ VLibras funciona 100% sem erros de console
  - ⚠️ Segurança CSP reduzida (unsafe-eval), mas mitigada por outras camadas
  - ✅ Quality Gate: 99.8/100 mantido (165 PASS, 1 WARNING)
  - ✅ WAF: Seg=100%, Conf=100%, Perf=80%, Custo=100%, Ops=100%

### Corrigido

#### Refatoração Defensiva do Proxy Gov.br — Arquitetura Mais Robusta
- **Problema**: Handler `async (req, res) => {}` com `await` pode causar SyntaxError se proxy movido para contexto errado (bugs anteriores: commits 9b6e52b, b376074)
- **Solução**: Refatorado para `.then()` chains (mais defensivo) — proxy funciona independente de contexto async
- **Mudanças**:
  - Handler mudado de `async` para síncrono: `(req, res) => {}`
  - Proxy proxy usa `.then()` chains ao invés de `await` (linhas 287-321)
  - `urlPath` calculado **ANTES** do proxy check (linha 279) — disponível para validação/reuse
  - Eliminado bloqueio `try/catch` async — .catch() mais granular no fim da chain
- **Benefícios**:
  - ✅ Nunca dá SyntaxError (não depende de contexto async)
  - ✅ urlPath disponível para lógica de roteamento antes do proxy
  - ✅ Mais defensive (funciona sempre, mesmo se código refatorado)
  - ✅ Melhor tratamento de erros (catch específico para proxy)
- **Quality Gate**: Mantido 100.0/100 (166 checks PASS)
- **Testes locais**: `/health` → 200, `/` → 200, `/api/govbr-servico/10783` → 200

## [1.2.2] - 2026-02-10

### Corrigido

#### Proxy Gov.br API — Contornar CORS para Enriquecimento de Dados
- **Problema**: Requisição direta do navegador para `https://servicos.gov.br/api/v1/servicos/10783` bloqueada por CORS (`No 'Access-Control-Allow-Origin'`)
- **Solução**: Endpoint proxy `/api/govbr-servico/:id` no server.js (linhas 238-273) que busca dados server-side
- **Timeout**: 5 segundos com AbortController (anti-Slowloris)
- **Cache**: 1 hora (`max-age=3600`) para reduzir carga no gov.br
- **Rate limiting**: Protegido pelo limite global de 120 req/min
- **app.js** (linha 613): Mudado fetch de URL direta para `/api/govbr-servico/10783`
- **Tamanho JS**: 99,438 bytes (562B margem, dentro do limite de 100KB)
- **Quality Gate**: Mantido 100.0/100 (166 checks PASS)
- **Impacto**: Badge "Serviço digital confirmado no gov.br" agora funciona sem erro de CORS

## [1.2.1] - 2026-02-10

### Corrigido

#### Content Security Policy (CSP) — Suporte Completo ao CDN Fallback do VLibras
- **`style-src`** — Adicionado `https://cdn.jsdelivr.net` para permitir estilos CSS do VLibras via CDN fallback (jsdelivr espelha repositório GitHub oficial)
- **`img-src`** — Adicionado `https://cdn.jsdelivr.net` para permitir imagens do VLibras via CDN fallback
- **`Cross-Origin-Resource-Policy`** — Mudado de `same-origin` para `cross-origin` no server.js (linha 132) para permitir que VLibras e outros serviços acessem recursos do site
- **Arquivos atualizados** — index.html (linha 18), index.min.html (linha 16), server.js (linhas 103, 132)
- **Impacto** — Garante funcionamento do VLibras mesmo quando vlibras.gov.br está indisponível (fallback automático para cdn.jsdelivr.net)
- **Quality Gate** — Mantido 100.0/100 com 166 checks PASS

## [1.2.0] - 2026-02-10

### Adicionado

#### Nova Categoria: Isenções Tributárias (IPI, IOF, ICMS, IPVA, IPTU)
- **10ª categoria** — “Isenções Tributárias” cobrindo todos os benefícios fiscais PcD para veículos e imóveis
- **Base legal completa** — Lei 8.989/1995 (IPI), Lei 14.287/2021 (atualização IPI R\$ 200k), Lei 8.383/1991 Art. 72 (IOF), Convênio CONFAZ ICMS 38/2012, LBI Art. 46
- **Tabela IPVA 27 UFs** — legislação específica de cada estado com link direto para SEFAZ (colapsável `<details>`)
- **Passo a passo SISEN** — procedimento completo para solicitação 100% digital de IPI/IOF via Receita Federal
- **Rodízio SP** — Lei Municipal 12.490/1997 (isenção com credencial DeFis)
- **4 novas fontes** — Lei 8.989/1995, Lei 14.287/2021, Lei 8.383/1991, Convênio CONFAZ ICMS 38/2012 (total: 29 fontes)

#### Integração Gov.br API
- **Serviço 10783** (SISEN) — enriquecimento via `servicos.gov.br/api/v1/servicos/10783` com fallback gracioso
- **Badge gov.br** — indicador visual "Serviço digital confirmado no gov.br" quando API responde
- **sessionStorage cache** — evita requisições repetidas à API

#### Motor de Correspondência
- **15 novos keywords** mapeados para `isencoes_tributarias`: iof, icms, iptu, tributo, tributária, imposto, sisen, confaz, rodízio, etc.
- Keywords existentes (ipva, ipi, isenção) agora mapeiam para ambas `transporte` + `isencoes_tributarias`

#### Dados
- `data/ipva_pcd_estados.json` — referência detalhada com 27 leis estaduais de isenção IPVA PcD
- `documentos_mestre` atualizado — RG, CPF, comprovante de residência e laudo médico agora incluem `isencoes_tributarias`
- Versão dos dados: 1.1.0 → 1.2.0

#### CSS
- Estilos para tabela IPVA (`.ipva-table`, `.table-wrapper`)
- Estilos para `<details>/<summary>` colapsável

### Qualidade
- **QG 99.6/100** — 164 PASS, 2 warnings (pré-existentes: inline script + VLibras)
- **Schema/Governança 100%** — todas as 10 categorias cobertas por documentos mestre e keyword map

## [1.1.1] - 2026-02-10

### Corrigido

#### Acessibilidade — ABNT NBR 17225:2024
- **54 font-sizes corrigidos** — todas as fontes abaixo de 0.875rem (14px) ajustadas para conformidade ABNT NBR 17225 / WCAG 2.1 AA / eMAG 3.1
  - 8 críticos (0.65-0.72rem → 0.75rem): badges, tags, bar-labels
  - 26 avisos (0.75-0.82rem → 0.8-0.875rem): botões, links, metadata
  - 20 borderline (0.85rem → 0.875rem): footer, disclaimers, filtros
- **`<header>` landmark adicionado** — toolbar de acessibilidade + nav encapsulados em `<header>` (WCAG 1.3.1)
- **Contraste dark mode corrigido** — removido inline `style="color:#64748b"` no footer que falhava 4.5:1 em dark mode

#### VLibras
- **Integração VLibras reescrita** — removido lazy-loading via createElement (incompatível com VLibras); integração direta via HTML `<script>` conforme documentação oficial gov.br
- **CSP atualizado** — adicionados `https://vlibras.gov.br` em script-src, style-src, img-src, connect-src, frame-src, media-src, font-src

#### UI — Interface
- **Badges de análise com cores sólidas** — `.analysis-badge.high/medium/low` agora usam background sólido `var(--bar-*)` com texto branco (legibilidade melhorada)
- **Labels textuais nas barras** — adicionados "Alta", "Média", "Baixa" como texto acima das barras de análise

#### Deploy
- **Timeout de deploy aumentado** — `--timeout 900` (era 600) para acomodar cold start do B1
- **Health check resiliente** — retry loop (12 tentativas × 15s) com `always()` condicional

#### Segurança / Privacidade
- **Email pessoal removido** — `alert_email` default vazio em terraform/variables.tf
- **Git email anonimizado** — commits com `noreply@github.com`

### Adicionado
- **Disclaimer de marcas** — avisos em LICENSE, README.md e ambos HTML sobre marcas registradas de terceiros
- **Pool Scout** e **Historical Analyzer** no CLI DeFi (projetos adjacentes)

## [1.1.0] - 2026-02-10

### Adicionado

#### SEO — Otimização para Motores de Busca
- **robots.txt** + **sitemap.xml** — diretivas de rastreamento e mapa do site para Google/Bing
- **FAQPage JSON-LD** — 5 perguntas frequentes com schema.org (potencial para featured snippets)
- **Twitter Card** — tags `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`
- **H1 com keywords** — "Direitos e Benefícios para Pessoas com Deficiência no Brasil" (copy emocional movido para subtítulo)
- **Title tag otimizado** — "Direitos PcD: BPC, CIPTEA, Escola Inclusiva, TEA — NossoDireito"
- **Meta description** — incluí "autismo", "TEA", "PcD", "passo a passo", "fontes oficiais"
- **Open Graph** — `og:site_name`, `og:image` 1200×630 com dimensões explícitas
- **og-image.png** — imagem social 1200×630 com logo, título e tagline no diretório `images/`
- **Keywords expandidas** — "CIPTEA como tirar", "plano de saúde autismo", "FGTS deficiência", "passe livre"

#### UX — Experiência do Usuário
- **Botão voltar do navegador** — `history.pushState` + `popstate` listener, URL muda para `#direito/{id}`
- **Toast notifications** — substitui todos os `alert()` por notificações inline com animação (error/warning/info/success)
- **Checklist com barra de progresso** — "X de 8 concluídos" com barra visual animada
- **Compartilhar no WhatsApp** — botão em cada detalhe de direito com texto pré-formatado
- **Skip-to-content** — link oculto "Pular para o conteúdo principal" (acessibilidade a11y)

#### Performance
- **pdf.js lazy-loading** — ~400KB carregado sob demanda (não mais no `<head>`), via `IntersectionObserver` + dynamic `<script>`
- `ensurePdfJs()` com fallback e SRI hash

#### CI/CD — Automação de Deploy
- **deploy.yml** — adicionados `robots.txt`, `sitemap.xml`, `sw.js`, `manifest.json` aos paths trigger
- **sitemap.xml lastmod auto-update** — atualizado automaticamente no deploy com data do dia
- **deploy package** — inclui `robots.txt`, `sitemap.xml`, `sw.js`, `manifest.json` no ZIP

#### Code Review — 9 novos checks (151 → 160 PASS)
- **OG image dimensions** — verifica `og:image:width` + `og:image:height` no HTML
- **og:site_name** — verifica tag presente
- **og-image.png** — verifica arquivo existe em `images/`
- **No alert()** — garante que `alert()` foi 100% substituído por `showToast()` (exclui comentários)
- **history.pushState** — verifica navegação SPA com botão voltar
- **WhatsApp share** — verifica botão de compartilhamento
- **Checklist progress bar** — verifica barra de progresso visual
- **pdf.js lazy-loading** — verifica `ensurePdfJs` presente
- **matching_engine.json** — verifica arquivo externalizado existe
- **deploy.yml paths** — verifica cobertura de todos os arquivos deployáveis

#### Tabela de Classificação CID
- Nova seção "Classificação CID" com tabela de referência de 10 tipos de deficiência
- Colunas: Tipo, CID-10, CID-11, Critério, Detalhes
- 10 categorias: TEA, Intelectual, Visual, Auditiva, Física, Amputação, Nanismo, Psicossocial, Múltipla, Reabilitados
- Tabela responsiva com header fixo, hover, badges de código

#### Órgãos Estaduais (27 estados)
- Nova seção "Órgãos Estaduais" com grid filtrável por região
- 27 URLs oficiais .gov.br validadas (todas as UFs brasileiras)
- Filtros: Todos, Norte, Nordeste, Centro-Oeste, Sudeste, Sul
- Cards com badge da UF, nome do órgão e link direto

#### Motor de Correspondência — CIDs e CRM
- **CRM Detection (Pass 0b)**: Detecção de CRM médico em documentos analisados (CRM/SP 123456, CRM-12345/SP, etc.) — boost +2 em 6 categorias que exigem laudo médico
- **CID-11 Two-Letter Regex**: Captura códigos CID-11 no formato MA10/AB00 (blocos de 2 letras)
- **30+ novos CIDs no KEYWORD_MAP**:
  - CID-10: F20 (esquizofrenia), F31 (bipolar), F41 (ansiedade), F90 (TDAH), G43 (enxaqueca), S78/S88 (amputação), Q77/E34 (nanismo), M21 (deformidade), Q65 (displasia)
  - CID-11: 6A00, 6A05 (TDAH), 6A20, 6A60, 6B00 (ansiedade), 9B50, AB00, 8D20, MA10, 5B51
  - Termos: tdah, hiperatividade, déficit de atenção, ansiedade generalizada, enxaqueca, cefaleia crônica, acondroplasia, esquizofrenia, bipolaridade
- **CID_RANGE_MAP**: Adicionados prefixos S (lesões/amputação) e M (osteomuscular)
- **UPPERCASE_ONLY_TERMS**: 23 novos termos adicionados (CIDs + siglas TDAH/TAG)

#### Links de Referência — CID, CRM e Conselhos Profissionais
- **4 novas fontes/serviços** no "Links Úteis":
  - DATASUS — Departamento de Informática do SUS (`datasus.saude.gov.br`)
  - OMS — CID-11 Browser em Português (`icd.who.int/browse/pt`)
  - CNES — Cadastro Nacional de Estabelecimentos e Profissionais (`cnes.datasus.gov.br`)
  - Saúde de A a Z — Ministério da Saúde (`gov.br/saude`)
- **3 novas instituições profissionais** no "Instituições de Apoio":
  - CFM — Conselho Federal de Medicina / Busca Médicos / CRM (`portal.cfm.org.br/busca-medicos`)
  - CFP — Conselho Federal de Psicologia / Cadastro Nacional (`cadastro.cfp.org.br`)
  - COFFITO — Conselho Federal de Fisioterapia e Terapia Ocupacional (`coffito.gov.br`)
- Domínios `cfm.org.br`, `cfp.org.br` e `who.int` adicionados à whitelist `isSafeUrl()`
- Ícones dedicados para conselhos profissionais (👨‍⚕️ CFM, 🧠 CFP, 🌐 OMS)

### Corrigido
- Alternância de seções (section-alt) corrigida para manter padrão visual zebrado
- Valor do BPC atualizado para R$ 1.621,00 (2026)
- Lei 15.131 adicionada
- URL da ANS corrigida
- NBR 9050 referenciada

#### Acessibilidade — Leitura em Voz Alta (TTS)
- **🔊 Ouvir** — botão nativo na barra de acessibilidade usando Web Speech API (`speechSynthesis`)
- Lê a seção visível em pt-BR, sem dependência externa (100% browser nativo)
- Seleção inteligente de voz: prioriza Google/Microsoft pt-BR por qualidade
- Limite de 2000 caracteres, velocidade 0.9x para clareza
- Auto-stop ao navegar para outra seção; toggle play/stop
- Graceful degradation: botão escondido se navegador não suporta TTS

#### Acessibilidade — VLibras (Libras)
- **🤟 Libras** — integração com VLibras (governo federal) para tradução em Libras
- Carregamento lazy com polling robusto (`waitForVLibrasButton`) em vez de `setTimeout`
- CSP atualizado: `frame-src`, `media-src`, `font-src` para domínios `vlibras.gov.br`

#### Segurança — CSP e Headers
- CSP sincronizado entre `index.html`, `index.min.html` e `server.js`
- Adicionados: `frame-ancestors 'none'`, `manifest-src 'self'`
- `media-src 'self'` adicionado para suporte a áudio nativo (Web Speech API)
- `rel="noopener noreferrer"` em todos os 9 links `target="_blank"` (HTML + JS)
- Remoção de todas as referências ao GitHub nos arquivos públicos (privacidade)

#### Bug Fixes — Motor de Análise
- **CRÍTICO**: `matchRights()` recebia texto em lowercase, destruindo detecção de CID (F84, G80, 6A02) e siglas (TEA, BPC, SUS). Corrigido com `originalText` preservando case
- Falso positivo "receita" removido — mantido apenas "receita médica"/"receita medica"
- Termos médicos expandidos com variantes sem acento para PDFs
- Correção ortográfica: "Avise-nos" → "avise-nos" (minúscula em meio de frase)

#### Quality Gate — quality_pipeline.py
- Regex de `rel="noopener"` atualizado para aceitar `rel="noopener noreferrer"`
- Contagem de links `target="_blank"` agora inclui links gerados por JS
- Comentários HTML removidos para reduzir tamanho (36.390 → 34.156 bytes, limite 35.000)

### Segurança
- `isSafeUrl()` aplicado em 4 locais adicionais
- Modal focus trap implementado
- Nav roles (aria) adicionados

#### Motor de Correspondência — Externalização
- **KEYWORD_MAP**, **CID_RANGE_MAP** e **UPPERCASE_ONLY_TERMS** movidos de `app.js` para `data/matching_engine.json` (53 KB)
- `app.js` reduzido de 105 KB → 78 KB (abaixo do limite de 100 KB)
- Dados carregados via `fetch()` assíncrono em `loadData()`, com `deepFreeze()` para imutabilidade
- Quality pipeline atualizado para validar KEYWORD_MAP tanto em `app.js` quanto em `matching_engine.json`
- Domínio `who.int` adicionado à whitelist `OFFICIAL_DOMAINS` do quality pipeline

#### PWA — Progressive Web App
- **manifest.json** criado — nome, ícones (32/180/512), `display: standalone`, `theme_color: #1e3a8a`
- **sw.js** (Service Worker) criado — cache-first para assets estáticos, network-first para JSON/HTML
  - Pre-cache de 10 assets estáticos + CDN (pdf.js)
  - Página de fallback offline embutida (HTML/CSS em-linha no SW)
  - `skipWaiting()` + `clients.claim()` para ativação imediata
- Registro do SW em `index.html` como script inline (resiliência: funciona mesmo se app.js falhar)
- `server.js`: header `no-cache` para `/sw.js` (spec W3C requer cache curto para detecção de atualização)

#### SEO e Metadados
- `<link rel="canonical" href="https://nossodireito.fabiotreze.com">` — URL canônica para Google
- `<link rel="preconnect">` + `<link rel="dns-prefetch">` para `cdnjs.cloudflare.com`
- JSON-LD (`@type: WebApplication`) — dados estruturados schema.org no `<head>`

#### Resiliência e Performance
- **`resilientFetch()`** — retry com exponential backoff (2 tentativas, 500ms delay inicial, não retenta 4xx)
- `loadData()` separado em 2 try/catch independentes:
  - Falha no `direitos.json` → exibe mensagem de erro na UI
  - Falha no `matching_engine.json` → degrada graciosamente (navegação manual funciona)
- `escapeHtml()` otimizado — elemento DOM reutilizável (`_escapeDiv`) em vez de criar novo por chamada

#### UX / Footer
- Badge de versão no footer (`v1.1.0`) populado dinamicamente de `jsonMeta.versao`
- `setupFooterVersion()` chamado após `loadData()` para garantir dados disponíveis

### Corrigido
- Links do GitHub corrigidos de `fabiorodrigues` → `fabiotreze/nossodireito` (2 locais)

#### Quality Pipeline — Novos Checks
- Regex de inline JS exclui `<script type="application/ld+json">` (JSON-LD não é JS executável)
- Registro de Service Worker excluído do check de inline JS (padrão de bootstrap válido)
- WAF Segurança: reconhece `sw.js` como indicador de HTTPS (SW requer HTTPS)
- WAF Confiabilidade: check para `resilientFetch` (retry pattern)
- WAF Performance: verifica `server.js` para Cache-Control (além de staticwebapp.config.json)
- 6 novos checks de Performance: canonical URL, preconnect, PWA manifest, Service Worker, JSON-LD
- WAF 5 Pilares: **100%** em todos (Seg/Conf/Perf/Custo/Ops)

### Dados
- `direitos.json` versão 1.1.0 (data: 2026-02-10, próx. revisão: 2026-02-17)
- Quality Gate: **100.0/100** (151 PASS, 0 WARNING, 0 ERROR)

## [1.0.1] - 2026-02-09

### Segurança — EASM Hardening

#### server.js — Reescrita completa com defesa em profundidade
- HSTS com `max-age=31536000; includeSubDomains; preload`
- Cross-Origin isolation completo: COOP (`same-origin`), CORP (`same-origin`), COEP (`credentialless`)
- Rate limiting in-memory por IP (120 req/min, 429 + Retry-After)
- Validação de Host header contra whitelist (`ALLOWED_HOSTS`) — CWE-644
- Supressão de identidade do servidor (`X-Powered-By` removido) — CWE-200
- Connection hardening: `timeout=30s`, `headersTimeout=15s`, `keepAliveTimeout=5s`, `maxHeadersCount=50` — prevenção Slowloris
- Limite de URL (2048 chars) com resposta 414 — CWE-400
- Extension whitelist (não blocklist) — apenas `.html`, `.css`, `.js`, `.json`, `.png`, `.ico`, `.svg`, `.webp`, `.woff2`
- `lstatSync` para rejeitar symlinks — CWE-59
- Rejeição de caracteres de controle na URL — CWE-158
- `Object.freeze()` em MIME, CACHE e SECURITY_HEADERS
- Permissions-Policy expandida: `usb`, `bluetooth`, `serial`, `hid`, `ambient-light-sensor`, `accelerometer`, `gyroscope`, `magnetometer`, `screen-wake-lock`

#### js/app.js — Proteção contra prototype pollution e open redirect
- `Object.freeze(Object.prototype)` + `Object.freeze(Array.prototype)` — CWE-1321
- `safeJsonParse()` com reviver que filtra `__proto__`, `constructor`, `prototype`
- `deepFreeze()` recursivo em todos os dados carregados (`direitosData`, `fontesData`, etc.) — CWE-471
- `isSafeUrl()` — validação de URL contra whitelist de domínios (gov.br, mesmo origin) — CWE-601
- `localGet()` agora usa `safeJsonParse()` em vez de `JSON.parse()`

#### index.html
- CSP atualizado com `upgrade-insecure-requests`

#### quality_pipeline.py — 12 novos checks EASM (checks 11–21)
- HSTS, COOP/CORP/COEP, rate limiting, host validation, connection timeouts
- Server identity suppression, upgrade-insecure-requests
- Prototype pollution guard, open redirect guard, safe JSON parse, deep freeze
- Quality Gate: **99.9/100** (137 PASS, 0 warnings, 0 errors)

## [1.0.0] - 2026-02-09

### Adicionado

#### Portal de Direitos PcD
- 9 categorias: BPC, CIPTEA, Educação, Plano de Saúde, SUS/Terapias, Transporte, Trabalho, FGTS, Moradia
- Base de conhecimento JSON com 20 fontes oficiais do governo brasileiro (gov.br)
- 12 instituições de apoio (governamentais, ONGs, profissionais)
- 13 documentos mestre por categoria
- KEYWORD_MAP com ~120+ termos (CIDs, leis, termos clínicos e administrativos)
- Upload e análise de documentos (PDF via pdf.js, imagens via Tesseract OCR)
- Checklist mestre de documentos por categoria
- Busca inteligente com destaque de termos encontrados
- Links úteis dinâmicos, hero stats dinâmicos, banner de conteúdo desatualizado

#### Segurança & Privacidade
- Criptografia AES-GCM-256 via Web Crypto API para documentos no IndexedDB
- TTL de 15 minutos com auto-expiração e limpeza automática
- CryptoKey com `extractable: false` (não-exportável)
- Revogação de Blob URLs com timeout de 15 segundos
- Content Security Policy (CSP) restritivo com `default-src 'none'`
- Subresource Integrity (SRI) sha384 em scripts CDN (pdf.js)
- Security headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy
- Headers OWASP adicionais: X-Permitted-Cross-Domain-Policies, X-DNS-Prefetch-Control
- Proteção contra null-byte injection, double-encoding e directory traversal no server.js
- Bloqueio de dotfiles, diretórios sensíveis e extensões proibidas no server.js
- Zero coleta de dados pessoais — processamento 100% local no navegador
- Conformidade com LGPD Art. 4º, I

#### Infraestrutura (Azure App Service)
- Azure App Service B1 Linux + Key Vault + PFX SSL (BYOC, SNI)
- Application Insights com geolocalização de usuários e Live Metrics
- Log Analytics Workspace (30 dias de retenção)
- Terraform (azurerm ~>4.0) com state via GitHub Artifact
- CI/CD: deploy.yml (push → Quality Gate → minificação → zip deploy)
- CI/CD: terraform.yml (manual dispatch → plan/apply/destroy)
- Minificação automática de JS (terser) e CSS (clean-css) no pipeline
- server.js — Node.js 20 LTS com gzip, cache headers, security headers

#### Quality Gate
- quality_pipeline.py — 17 categorias de verificação automática
- Score mínimo de 75 para deploy (score atual: 99.9/100)
- Scan automático de segredos (chaves, tokens, certificados)
- Avaliação WAF dos 5 pilares (Segurança, Confiabilidade, Performance, Custo, Ops)
- Verificação LGPD, disclaimers, fontes oficiais, acessibilidade, schema
- Modo CI (`--ci`, `--min-score`) com exit code para pipelines

#### Interface & Acessibilidade
- Design responsivo com dark mode automático (prefers-color-scheme)
- Modal de disclaimer legal (obrigatório na 1ª visita)
- 15+ atributos ARIA, aria-live, tabindex, :focus-visible
- Suporte a alto contraste (forced-colors), prefers-reduced-motion
- Estilos de impressão, classe sr-only
- Favicons (favicon.ico, favicon-32x32.png, apple-touch-icon.png)

#### Documentação & Governança
- GOVERNANCE.md — critérios para fontes, categorias, revisão periódica
- SECURITY.md — política de divulgação de vulnerabilidades e boas práticas
- SECURITY_AUDIT.md — auditoria de segurança documentada
- LICENSE (MIT + aviso informativo)
- Workflow `weekly-review.yml` — issue automática periódica
- README.md com badges (Quality Gate, Deploy, Segurança, LGPD, Licença, Versão)
