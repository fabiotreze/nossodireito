# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

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
