# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

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

#### Quality Gate — codereview.py
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
- Codereview atualizado para validar KEYWORD_MAP tanto em `app.js` quanto em `matching_engine.json`
- Domínio `who.int` adicionado à whitelist `OFFICIAL_DOMAINS` do codereview

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

#### Codereview — Novos Checks
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

#### codereview.py — 12 novos checks EASM (checks 11–21)
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
- codereview.py v2.0.0 — 17 categorias de verificação automática
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
- GOVERNANCE.md — critérios para fontes, categorias, revisão semanal
- SECURITY.md — política de divulgação de vulnerabilidades e boas práticas
- SECURITY_AUDIT.md — auditoria de segurança documentada
- LICENSE (MIT + aviso informativo)
- Workflow `weekly-review.yml` — issue automática toda segunda-feira
- README.md com badges (Quality Gate, Deploy, Segurança, LGPD, Licença, Versão)
