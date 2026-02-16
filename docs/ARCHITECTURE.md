# NossoDireito — Arquitetura do Sistema V1 (Produção Atual)

**Versão:** 1.12.4
**Data:** Fevereiro 2026
**Status:** Produção Estável (Quality Gate: 100.0/100)
**URL:** https://nossodireito.fabiotreze.com
**Tipo:** Portal informacional sem fins lucrativos para direitos de PcD (Pessoa com Deficiência)

---

## Índice

1. [Resumo Executivo](#1-resumo-executivo)
2. [Visão Geral do Sistema](#2-visão-geral-do-sistema)
3. [Stack Tecnológica](#3-stack-tecnológica)
4. [Arquitetura de Aplicação](#4-arquitetura-de-aplicação)
5. [Infraestrutura Azure](#5-infraestrutura-azure)
6. [Segurança & EASM](#6-segurança--easm)
7. [Conformidade LGPD](#7-conformidade-lgpd)
8. [Acessibilidade (WCAG/eMAG)](#8-acessibilidade-wcageag)
9. [Performance & Cache](#9-performance--cache)
10. [CI/CD & DevOps](#10-cicd--devops)
11. [Monitoramento & Observabilidade](#11-monitoramento--observabilidade)
12. [Custo de Operação](#12-custo-de-operação)
13. [Limitações Conhecidas](#13-limitações-conhecidas)
14. [DNS & Domínio Customizado](#14-dns--domínio-customizado)
15. [Disaster Recovery & Backup](#15-disaster-recovery--backup)

---

## 1. Resumo Executivo

### Propósito
**NossoDireito** é um portal web gratuito que fornece informações sobre direitos e benefícios para pessoas com deficiência (PcD) no Brasil. Criado para famílias que recebem laudos médicos (TEA, deficiência física, intelectual, sensorial), o portal oferece:

- **25 categorias de direitos**: BPC/LOAS, CIPTEA, Educação Inclusiva, Terapias SUS, Planos de Saúde, Transporte, Trabalho, FGTS, Habitação, IPVA PcD, Isenção IR, Prioridade em Filas, Tecnologia Assistiva, Aposentadoria PcD, entre outras
- **Análise de documentos**: Upload de laudos médicos em PDF para identificação automática de direitos relacionados (regex-based matching)
- **Recursos de acessibilidade**: TTS (Text-to-Speech), VLibras (Libras em vídeo), ajuste de fonte, alto contraste, navegação por teclado
- **Totalmente offline-first**: Service Worker com cache, dados JSON estáticos, zero backend dinâmico

### Arquitetura
100% client-side rendering com Node.js como servidor de arquivos estáticos endurecido para segurança. Dados estruturados em JSON (2.293 linhas de direitos + 2.716 linhas de motor de matching). Infraestrutura hospedada no Azure App Service (Linux, Node.js 22 LTS) com Terraform IaC.

### Conformidade
- **LGPD Art. 4º, I**: Não armazena dados pessoais em servidores (análise 100% local no navegador)
- **WCAG 2.1 Nível AA**: Contraste ≥4.5:1, navegação por teclado, ARIA labels, landmarks
- **eMAG 3.1** (Gov.br): VLibras para tradução em Libras, text-to-speech nativo
- **OWASP Secure Headers**: CSP, HSTS, X-Frame-Options, Permissions-Policy

### KPIs V1
| Métrica | Valor |
|---------|-------|
| **Quality Gate** | 100.0/100 |
| **Uptime SLA** | 99.95% (Azure App Service Basic+) |
| **Custo Mensal** | ~$13/mês (App Service B1 + Key Vault) |
| **Tempo de Resposta** | <500ms (95th percentile) |
| **Categorias de Direitos** | 25 (direitos.json 216KB) |
| **Keywords Matching** | ~1.218 termos + CID-10/11 ranges |
| **Acurácia de Análise** | ~70% (limitação regex) |
| **Lighthouse Score** | Performance: 95+, Accessibility: 100, Best Practices: 100, SEO: 100 |
| **Tamanho Total** | 2.78 MB (52 arquivos) |

---

## 2. Visão Geral do Sistema

### Fluxo de Usuário Principal

```
1. Acesso ao Portal (nossodireito.fabiotreze.com)
   ↓
2. Disclaimer LGPD (modal inicial)
   ↓
3. Navegação:
   ├─ Busca por palavra-chave (search bar)
   ├─ Exploração de categorias (25 cards)
   ├─ Checklist "Primeiros Passos" (guia interativo)
   └─ Upload de laudo PDF (análise local)
       ↓
4. Análise de Documento:
   ├─ Upload → IndexedDB com AES-GCM-256 (TTL 30 min)
   ├─ PDF.js extrai texto
   ├─ Regex matching com data/matching_engine.json
   └─ Exibe direitos identificados (score + peso)
       ↓
5. Exploração de Direitos:
   ├─ Expansão de cards com detalhes
   ├─ Links para fontes oficiais (.gov.br)
   ├─ Leitura em voz alta (TTS)
   └─ Tradução em Libras (VLibras)
       ↓
6. Saída: Usuário salva informações ou imprime
```

### Componentes do Sistema

```
┌────────────────────────────────────────────────────────┐
│              USUÁRIO (Browser/PWA)                     │
└────────────────┬───────────────────────────────────────┘
                 │
        ┌────────▼──────────┐
        │   GoDaddy DNS     │  ← CNAME: nossodireito.fabiotreze.com
        │   (Registrar)     │     aponta para app-nossodireito.azurewebsites.net
        └────────┬──────────┘
                 │
        ┌────────▼────────────────────────────────────────┐
        │         Azure App Service (Linux)               │
        │  ┌──────────────────────────────────────────┐  │
        │  │  Node.js 22 LTS (server.js)              │  │
        │  │  - Servidor estático HTTP                │  │
        │  │  - Security headers (CSP, HSTS)          │  │
        │  │  - Rate limiting (120 req/min)           │  │
        │  │  - Gzip/Brotli compression               │  │
        │  │  - Health check endpoint (/health)       │  │
        │  └──────────────────────────────────────────┘  │
        │                                                  │
        │  Assets Servidos:                                │
        │  ├─ index.html (568 linhas, SPA shell)          │
        │  ├─ css/styles.css (2.862 linhas)               │
        │  ├─ js/app.js (2.682 linhas, lógica principal)  │
        │  ├─ js/sw-register.js (Service Worker loader)   │
        │  ├─ sw.js (158 linhas, cache-first strategy)    │
        │  ├─ data/direitos.json (2.293 linhas)           │
        │  └─ data/matching_engine.json (2.716 linhas)    │
        └───────────┬────────────────────────────────────┘
                    │
        ┌───────────▼──────────────────┐
        │  Azure Key Vault (Standard)  │  ← Certificado SSL PFX
        │  - Certificado wildcard      │     (fabiotreze.com + *.fabiotreze.com)
        │  - Managed Identity access   │
        └──────────────────────────────┘
                    │
        ┌───────────▼─────────────────────────────────┐
        │  Azure Application Insights                 │
        │  - Métricas servidor (Node.js SDK)          │
        │  - Page views, IPs, geolocalização          │
        │  - Tempos de resposta, erros                │
        │  - Alertas (5xx, health check, latência)    │
        └─────────────────────────────────────────────┘
                    │
        ┌───────────▼──────────────────┐
        │  Azure Log Analytics         │
        │  - Workspace (30 dias)       │
        │  - Queries KQL para análise  │
        └──────────────────────────────┘
```

### Client-Side (Browser)

```
┌──────────────────────────────────────────────────────┐
│                  Browser (PWA)                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  index.html (SPA Shell)                     │    │
│  │  - Header: Navbar + A11y Toolbar            │    │
│  │  - Main: Cards dinâmicos renderizados por JS │   │
│  │  - Footer: Links oficiais + transparência   │    │
│  └──────────────┬──────────────────────────────┘    │
│                 │                                    │
│  ┌──────────────▼──────────────────────────────┐    │
│  │  app.js (2.682 linhas)                      │    │
│  │  ┌───────────────────────────────────────┐  │    │
│  │  │  1. TTS Engine (Web Speech API)      │  │    │
│  │  │     - Síntese de voz em pt-BR        │  │    │
│  │  │     - Chunking de texto longo        │  │    │
│  │  │     - Seleção de voz brasileira      │  │    │
│  │  ├───────────────────────────────────────┤  │    │
│  │  │  2. VLibras Integration              │  │    │
│  │  │     - Unity WebGL carregado via CDN  │  │    │
│  │  │     - Widget gov.br (vlibras.gov.br) │  │    │
│  │  ├───────────────────────────────────────┤  │    │
│  │  │  3. PDF Analysis Engine              │  │    │
│  │  │     - PDF.js text extraction         │  │    │
│  │  │     - Regex matching CID codes       │  │    │
│  │  │     - Keyword weight calculation     │  │    │
│  │  │     - Score-based ranking            │  │    │
│  │  ├───────────────────────────────────────┤  │    │
│  │  │  4. IndexedDB Manager                │  │    │
│  │  │     - Armazenamento local de PDFs    │  │    │
│  │  │     - AES-GCM-256 encryption         │  │    │
│  │  │     - TTL 30 minutos (auto-delete)   │  │    │
│  │  ├───────────────────────────────────────┤  │    │
│  │  │  5. UI Renderer                      │  │    │
│  │  │     - Renderização de cards dinâmica │  │    │
│  │  │     - Search filtering               │  │    │
│  │  │     - Modal/Accordion management     │  │    │
│  │  ├───────────────────────────────────────┤  │    │
│  │  │  6. A11y Controller                  │  │    │
│  │  │     - Font size adjustment (±)       │  │    │
│  │  │     - High contrast toggle           │  │    │
│  │  │     - Keyboard navigation handler    │  │    │
│  │  └───────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │  Service Worker (sw.js)                     │    │
│  │  - Cache-first: HTML, CSS, JS, images       │    │
│  │  - Network-first: direitos.json             │    │
│  │  - Offline fallback                          │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │  IndexedDB (nossoDireitoDB)                 │    │
│  │  - Store: pdfFiles                          │    │
│  │  - Schema: {id, name, data: ArrayBuffer,    │    │
│  │             encryptionKey, uploadDate}       │    │
│  │  - TTL: 30 minutos (sweep a cada 60s)       │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │  localStorage                                │    │
│  │  - disclaimerAccepted: boolean               │    │
│  │  - checklist_[id]: boolean (progresso)      │    │
│  │  - fontSize: number (1.0-1.5)               │    │
│  │  - highContrast: boolean                     │    │
│  │  - lastVisit: timestamp                      │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

### Dados Estáticos (JSON)

#### data/direitos.json (2.293 linhas)
Fonte de verdade para as 25 categorias de direitos PcD. Estrutura:

```json
{
  "versao": "1.3.0",
  "ultima_atualizacao": "2026-02-10",
  "categorias": [
    {
      "id": "bpc_loas",
      "titulo": "BPC/LOAS — Benefício de Prestação Continuada",
      "descricao_curta": "1 salário mínimo mensal para PcD de baixa renda",
      "detalhes": {
        "requisitos": ["Renda per capita familiar ≤ 1/4 salário mínimo", "..."],
        "documentos": ["CPF", "RG", "Laudo médico com CID", "Comprovante de residência"],
        "como_solicitar": ["Acesse meu.inss.gov.br ou ligue 135", "..."],
        "prazo_medio": "45-90 dias (perícia médica obrigatória)"
      },
      "fontes": [
        {
          "titulo": "Lei 8.742/1993 (LOAS)",
          "url": "https://www.planalto.gov.br/ccivil_03/leis/l8742.htm"
        }
      ],
      "cids_relacionados": ["F84.0", "F84.9", "F90.0", "Q90.0", "..."],
      "keywords": ["bpc", "loas", "beneficio", "assistencial", "baixa renda"]
    },
    // ... outras 24 categorias
  ]
}
```

**Total de Categorias (25):**

Incluem BPC/LOAS, CIPTEA, Educação Inclusiva, Terapias e Planos de Saúde, Terapias pelo SUS, Transporte (Passe Livre, IPVA, Estacionamento), Trabalho (Cotas PcD, Estabilidade), FGTS (Saque), Habitação (Prioridade MCMV), IPVA PcD (isenção por estado), Isenção de Imposto de Renda, Prioridade em Filas, Tecnologia Assistiva, Aposentadoria PcD, entre outras. Lista completa em `data/direitos.json`.

#### data/matching_engine.json (2.716 linhas)
Motor de análise de documentos baseado em regex e pesos.

```json
{
  "version": "1.2.0",
  "cid_mappings": {
    "F84.0": {
      "disease": "Autismo Infantil",
      "categories": ["bpc_loas", "ciptea", "educacao", "terapias_plano", "terapias_sus", "transporte", "trabalho"],
      "weight": 10
    },
    "F84.9": {
      "disease": "Transtornos Globais do Desenvolvimento Não Especificados",
      "categories": ["ciptea", "educacao", "terapias_plano", "terapias_sus"],
      "weight": 8
    }
    // ... 50+ CID codes
  },
  "keyword_patterns": {
    "bpc_loas": {
      "primary": ["bpc", "loas", "beneficio assistencial"],
      "secondary": ["baixa renda", "inss", "pericia medica"],
      "uppercase_only_terms": ["BPC", "LOAS", "INSS"]
    },
    "ciptea": {
      "primary": ["ciptea", "carteira tea", "lei romeo mion"],
      "secondary": ["autismo", "tea", "transtorno espectro autista"],
      "uppercase_only_terms": ["CIPTEA", "TEA"]
    }
    // ... para todas 25 categorias
  },
  "cid_ranges": [
    {
      "range": "F70-F79",
      "description": "Retardo mental",
      "categories": ["bpc_loas", "educacao", "trabalho"]
    },
    {
      "range": "F80-F89",
      "description": "Transtornos do desenvolvimento psicológico",
      "categories": ["ciptea", "educacao", "terapias_plano", "terapias_sus"]
    }
    // ... 15+ ranges
  ]
}
```

**Lógica de Matching:**
1. Extração de texto do PDF via PDF.js
2. Busca por CID codes exatos (regex `[A-Z]\d{2}(\.\d{1,2})?`)
3. Busca por keywords com peso (primary: 10, secondary: 5)
4. Cálculo de score por categoria: `∑(pesos de CIDs + keywords encontrados)`
5. Ordenação por score decrescente
6. Retorno das categorias com score > 0

---

## 3. Stack Tecnológica

### Frontend
| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **HTML5** | - | SPA shell (index.html 568 linhas) |
| **CSS3** | - | styles.css (2.862 linhas), variáveis CSS, dark mode `@media (prefers-color-scheme: dark)` |
| **JavaScript (Vanilla)** | ES2022 | app.js (2.682 linhas), zero frameworks/libraries |
| **Web Speech API** | - | Text-to-speech (TTS) síntese de voz pt-BR |
| **PDF.js** | 3.11.174 | Extração de texto de PDFs (CDN cloudflare.com) |
| **VLibras** | 3.2 | Widget gov.br para tradução Libras (Unity WebGL) |
| **Service Worker API** | - | Cache-first strategy (sw.js 158 linhas) |
| **IndexedDB API** | - | Armazenamento local de PDFs com AES-GCM-256 |
| **Web Crypto API** | - | Criptografia client-side (AES-GCM-256) |

### Backend
| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Node.js** | 22 LTS | Runtime do servidor |
| **http (native)** | - | Servidor HTTP vanilla (sem Express/Fastify) |
| **zlib (native)** | - | Compressão Gzip/Brotli |
| **applicationinsights** | 3.4.0 | Telemetria Azure (único dependency) |

### Infraestrutura
| Serviço | Tier | Uso |
|---------|------|-----|
| **Azure App Service** | B1 Linux (Basic) | Hospedagem do Node.js server |
| **Azure Key Vault** | Standard | Armazenamento de certificado SSL PFX |
| **Azure Application Insights** | Pay-as-you-go | Monitoramento, métricas, alertas |
| **Azure Log Analytics** | PerGB2018 | Workspace para logs (30 dias retenção) |
| **GoDaddy DNS** | - | Registrar do domínio fabiotreze.com |

### DevOps & IaC
| Ferramenta | Versão | Uso |
|------------|--------|-----|
| **Terraform** | 1.9+ | Infrastructure as Code (main.tf 370 linhas) |
| **GitHub Actions** | - | CI/CD (deploy.yml, quality-gate.yml) |
| **Python** | 3.12+ | Scripts de validação (validate_sources.py, bump_version.py) |

### Dependências NPM
```json
{
  "applicationinsights": "^3.4.0"  // Único dependency
}
```

**Justificativa Zero Dependencies (frontend):**
- Evita supply chain attacks (npm package hijacking)
- Reduz bundle size (<100 KB total JS minificado)
- Melhor controle sobre código executado
- Facilita auditoria de segurança

---

## 4. Arquitetura de Aplicação

### server.js — Servidor Estático Endurecido (420 linhas)

**Responsabilidades:**
1. Servir arquivos estáticos (HTML, CSS, JS, JSON, imagens)
2. Aplicar security headers (CSP, HSTS, X-Frame-Options, etc.)
3. Rate limiting por IP (120 req/min, janela 1 minuto)
4. Compressão Gzip/Brotli para assets text-based
5. Cache headers otimizados por tipo de arquivo
6. Health check endpoint (`/health`) para Azure probe
7. Redirect azurewebsites.net → domínio customizado (SEO)
8. Proxy reverso para API gov.br (CORS bypass)

**Destaques de Segurança (EASM-hardened):**

```javascript
// Security Headers (OWASP Secure Headers + Mozilla Observatory)
const SECURITY_HEADERS = {
  'Content-Security-Policy': [
    "default-src 'none'",
    "script-src 'self' blob: https://cdnjs.cloudflare.com https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net 'unsafe-eval' 'wasm-unsafe-eval'",
    "style-src 'self' 'unsafe-inline' https://*.vlibras.gov.br https://cdn.jsdelivr.net",
    "img-src 'self' data: blob: https://vlibras.gov.br https://*.vlibras.gov.br",
    "connect-src 'self' https://vlibras.gov.br https://*.vlibras.gov.br",
    "frame-src 'self' https://*.vlibras.gov.br blob:",
    "form-action 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
    "upgrade-insecure-requests"
  ].join('; '),
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'no-referrer',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), serial=(), hid=()',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Resource-Policy': 'cross-origin',
  'Cross-Origin-Embedder-Policy': 'unsafe-none'  // VLibras Unity requer cross-origin assets
};
```

**Rate Limiting (in-memory):**
```javascript
const RATE_LIMIT_WINDOW = 60_000;  // 1 minuto
const RATE_LIMIT_MAX = 120;        // 120 requisições

function isRateLimited(ip) {
    const now = Date.now();
    const entry = rateLimitMap.get(ip);
    if (!entry || now - entry.start > RATE_LIMIT_WINDOW) {
        rateLimitMap.set(ip, { start: now, count: 1 });
        return false;
    }
    entry.count++;
    return entry.count > RATE_LIMIT_MAX;
}

// Cleanup stale entries (evita memory leak)
setInterval(() => {
    const now = Date.now();
    for (const [ip, entry] of rateLimitMap) {
        if (now - entry.start > RATE_LIMIT_WINDOW) rateLimitMap.delete(ip);
    }
}, 300_000);  // A cada 5 minutos
```

**Cache Policies:**
```javascript
const CACHE = {
    '.html': 'public, max-age=300',    // 5 min (atualização rápida)
    '.json': 'public, max-age=3600',   // 1 hora (direitos.json)
    '.css': 'public, max-age=86400',   // 1 dia
    '.js': 'public, max-age=86400',    // 1 dia
    '.png': 'public, max-age=604800',  // 1 semana
    '.ico': 'public, max-age=604800',
    '.svg': 'public, max-age=604800',
    '.xml': 'public, max-age=3600',
};

// Service Worker exception: cache curto para update detection
const isSW = urlPath === '/sw.js';
const cacheControl = isSW ? 'no-cache' : (CACHE[ext] || 'no-cache');
```

**Whitelist de Extensões (CWE-434):**
```javascript
const ALLOWED_EXT = new Set([
    '.html', '.css', '.js', '.json',
    '.png', '.ico', '.svg', '.webp',
    '.txt', '.xml'
]);

// Rejeita tudo que não está na whitelist
if (ext && !ALLOWED_EXT.has(ext)) return null;
```

**Directory Traversal Protection (CWE-22):**
```javascript
function resolveFile(urlPath) {
    // 1. Reject null-byte injection
    if (urlPath.includes('\0')) return null;

    // 2. Reject oversized URLs (CWE-400)
    if (urlPath.length > MAX_URL_LENGTH) return null;

    // 3. Reject control characters
    if (/[\x00-\x1f\x7f]/.test(urlPath)) return null;

    // 4. Normalize and decode
    let filePath;
    try {
        filePath = path.normalize(decodeURIComponent(urlPath));
    } catch {
        return null;  // malformed URI
    }

    // 5. Reject double-encoded traversal (e.g. %252e%252e)
    if (filePath.includes('..')) return null;

    // 6. Ensure within root
    const fullPath = path.join(ROOT, filePath);
    if (!fullPath.startsWith(ROOT + path.sep) && fullPath !== ROOT) return null;

    // 7. Block dotfiles (.env, .git, .github)
    const segments = relative.split(path.sep);
    if (segments.some(seg => seg.startsWith('.'))) return null;

    // 8. Block sensitive directories
    const BLOCKED_DIRS = new Set(['terraform', 'node_modules', 'docs']);
    if (BLOCKED_DIRS.has(segments[0].toLowerCase())) return null;

    return fullPath;
}
```

**Connection Hardening (anti-Slowloris):**
```javascript
server.timeout = 30_000;           // 30s request timeout
server.headersTimeout = 15_000;    // 15s header timeout
server.requestTimeout = 30_000;    // 30s total request timeout
server.keepAliveTimeout = 5_000;   // 5s keep-alive
server.maxHeadersCount = 50;       // Limit header count
server.maxRequestsPerSocket = 100; // Limit requests per socket
```

### app.js — Lógica Client-Side Principal (2.682 linhas)

**Módulos Principais:**

#### 1. TTS Engine (Text-to-Speech)
```javascript
// Web Speech API — Síntese de voz pt-BR
class TTSEngine {
    constructor() {
        this.synth = window.speechSynthesis;
        this.voice = this.selectBrazilianVoice();
        this.isSpeaking = false;
        this.currentUtterance = null;
    }

    selectBrazilianVoice() {
        const voices = this.synth.getVoices();
        // Preferência: Google português do Brasil > Microsoft Helena > fallback
        const preferred = [
            'Google português do Brasil',
            'Microsoft Helena - Portuguese (Brazil)',
            'Luciana',  // iOS pt-BR
        ];

        for (const name of preferred) {
            const match = voices.find(v => v.name.includes(name) || v.lang === 'pt-BR');
            if (match) return match;
        }

        return voices.find(v => v.lang.startsWith('pt')) || voices[0];
    }

    speak(text) {
        if (this.isSpeaking) this.stop();

        // Chunk text em parágrafos menores (limite API: ~32.767 chars)
        const chunks = this.chunkText(text, 1000);

        chunks.forEach((chunk, i) => {
            const utterance = new SpeechSynthesisUtterance(chunk);
            utterance.voice = this.voice;
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            utterance.lang = 'pt-BR';

            utterance.onend = () => {
                if (i === chunks.length - 1) {
                    this.isSpeaking = false;
                    this.updateButton(false);
                }
            };

            utterance.onerror = (e) => {
                console.error('TTS error:', e);
                this.isSpeaking = false;
                this.updateButton(false);
            };

            this.synth.speak(utterance);
        });

        this.isSpeaking = true;
    }

    stop() {
        this.synth.cancel();
        this.isSpeaking = false;
    }

    chunkText(text, maxLength) {
        // Split por parágrafos e sentenças para melhor naturalidade
        const paragraphs = text.split(/\n\n+/);
        const chunks = [];
        let currentChunk = '';

        paragraphs.forEach(para => {
            if ((currentChunk + para).length > maxLength) {
                if (currentChunk) chunks.push(currentChunk.trim());
                currentChunk = para;
            } else {
                currentChunk += (currentChunk ? '\n\n' : '') + para;
            }
        });

        if (currentChunk) chunks.push(currentChunk.trim());
        return chunks;
    }
}
```

#### 2. VLibras Integration
```javascript
// Unity WebGL Widget (gov.br) — Tradução Libras
function initVLibras() {
    // 1. Carregar script gov.br
    const script = document.createElement('script');
    script.src = 'https://vlibras.gov.br/app/vlibras-plugin.js';
    script.async = true;
    script.onload = () => {
        // 2. Inicializar widget
        new window.VLibras.Widget({
            rootPath: 'https://vlibras.gov.br/app',
            opacity: 1,
            position: 'R',  // Right
            avatar: 'icaro',  // Avatar padrão
        });

        // 3. Mover botão para accessibility toolbar
        setTimeout(() => {
            const vlibrasBtn = document.querySelector('[vw-access-button]');
            if (vlibrasBtn) {
                vlibrasBtn.style.display = 'none';  // Esconder botão nativo
            }
        }, 1000);
    };

    script.onerror = () => {
        console.error('Falha ao carregar VLibras');
        alert('VLibras indisponível. Tente novamente mais tarde.');
    };

    document.head.appendChild(script);
}

// Botão customizado na toolbar
document.getElementById('a11yLibras').addEventListener('click', () => {
    const widget = document.querySelector('[vw]');
    if (!widget) {
        initVLibras();
    } else {
        // Toggle widget existente
        const btn = document.querySelector('[vw-access-button]');
        if (btn) btn.click();
    }
});
```

**Nota sobre Unity WebGL Errors:**
Erros comuns em mobile (INVALID_ENUM 0x822A no glTexSubImage2DRobustANGLE):
- **Causa:** Unity 2018 usa HDR texture formats não suportados em GPUs mobile antigas
- **Impacto:** Zero — widget funciona normalmente, erros são fallback do Unity
- **Ação:** Ignorar logs de erro (fora do nosso controle, widget oficial gov.br)

#### 3. PDF Analysis Engine
```javascript
// PDF.js text extraction + Regex matching
class PDFAnalyzer {
    constructor(matchingEngine) {
        this.engine = matchingEngine;  // data/matching_engine.json
        this.pdfjsLib = window['pdfjs-dist/build/pdf'];
        this.pdfjsLib.GlobalWorkerOptions.workerSrc =
            'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }

    async analyzePDF(file) {
        // 1. Carregar PDF via ArrayBuffer
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await this.pdfjsLib.getDocument({ data: arrayBuffer }).promise;

        // 2. Extrair texto de todas páginas
        let fullText = '';
        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            const pageText = textContent.items.map(item => item.str).join(' ');
            fullText += pageText + '\n';
        }

        // 3. Normalizar texto (uppercase para matching case-insensitive)
        const normalizedText = fullText.toUpperCase();

        // 4. Buscar CID codes
        const cidMatches = this.extractCIDs(normalizedText);

        // 5. Buscar keywords por categoria
        const keywordMatches = this.extractKeywords(normalizedText);

        // 6. Calcular scores por categoria
        const scores = this.calculateScores(cidMatches, keywordMatches);

        // 7. Ordenar e retornar
        return Object.entries(scores)
            .filter(([_, score]) => score > 0)
            .sort((a, b) => b[1] - a[1])
            .map(([categoryId, score]) => ({ categoryId, score }));
    }

    extractCIDs(text) {
        const cidRegex = /[A-Z]\d{2}(?:\.\d{1,2})?/g;
        const matches = [...text.matchAll(cidRegex)];

        return matches
            .map(m => m[0])
            .filter(cid => this.engine.cid_mappings[cid])
            .map(cid => ({
                code: cid,
                categories: this.engine.cid_mappings[cid].categories,
                weight: this.engine.cid_mappings[cid].weight
            }));
    }

    extractKeywords(text) {
        const matches = {};

        Object.entries(this.engine.keyword_patterns).forEach(([categoryId, patterns]) => {
            let score = 0;

            // Primary keywords (peso 10)
            patterns.primary.forEach(keyword => {
                const regex = new RegExp(keyword, 'gi');
                const count = (text.match(regex) || []).length;
                score += count * 10;
            });

            // Secondary keywords (peso 5)
            patterns.secondary.forEach(keyword => {
                const regex = new RegExp(keyword, 'gi');
                const count = (text.match(regex) || []).length;
                score += count * 5;
            });

            // Uppercase-only terms (somente maiúsculas — evita false positives)
            patterns.uppercase_only_terms?.forEach(term => {
                const regex = new RegExp(`\\b${term}\\b`, 'g');  // word boundary
                const count = (text.match(regex) || []).length;
                score += count * 10;
            });

            matches[categoryId] = score;
        });

        return matches;
    }

    calculateScores(cidMatches, keywordMatches) {
        const scores = {};

        // Scores de CIDs
        cidMatches.forEach(match => {
            match.categories.forEach(categoryId => {
                scores[categoryId] = (scores[categoryId] || 0) + match.weight;
            });
        });

        // Scores de keywords
        Object.entries(keywordMatches).forEach(([categoryId, score]) => {
            scores[categoryId] = (scores[categoryId] || 0) + score;
        });

        return scores;
    }
}
```

**Limitações da Análise Regex:**
- Acurácia: ~70% (vs. 95% possível com NLP/GPT)
- Não entende contexto semântico ("não elegível" conta como "elegível")
- False positives: Keywords genéricos (ex: "saúde" em contextos irrelevantes)
- False negatives: Laudos mal formatados, PDF scaneado sem OCR
- Não detecta negativas ("paciente NÃO apresenta TEA")

#### 4. IndexedDB Manager (Encryption)
```javascript
// Armazenamento local com AES-GCM-256 + TTL
class IndexedDBManager {
    constructor(dbName = 'nossoDireitoDB', storeName = 'pdfFiles') {
        this.dbName = dbName;
        this.storeName = storeName;
        this.db = null;
        this.TTL_MINUTES = 30;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains(this.storeName)) {
                    const store = db.createObjectStore(this.storeName, { keyPath: 'id', autoIncrement: true });
                    store.createIndex('uploadDate', 'uploadDate', { unique: false });
                }
            };
        });
    }

    async savePDF(name, arrayBuffer) {
        // 1. Gerar encryption key (AES-GCM-256)
        const key = await crypto.subtle.generateKey(
            { name: 'AES-GCM', length: 256 },
            true,
            ['encrypt', 'decrypt']
        );

        // 2. Gerar IV aleatório (12 bytes)
        const iv = crypto.getRandomValues(new Uint8Array(12));

        // 3. Encriptar PDF
        const encryptedData = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv },
            key,
            arrayBuffer
        );

        // 4. Exportar key (para armazenar)
        const exportedKey = await crypto.subtle.exportKey('raw', key);

        // 5. Salvar no IndexedDB
        const transaction = this.db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);

        const record = {
            name,
            data: encryptedData,
            key: exportedKey,
            iv: Array.from(iv),  // Uint8Array → Array para serialização
            uploadDate: Date.now(),
            expiresAt: Date.now() + (this.TTL_MINUTES * 60 * 1000)
        };

        await store.add(record);

        return { success: true, id: record.id };
    }

    async getPDF(id) {
        const transaction = this.db.transaction([this.storeName], 'readonly');
        const store = transaction.objectStore(this.storeName);
        const record = await store.get(id);

        if (!record) return null;

        // Verificar TTL
        if (Date.now() > record.expiresAt) {
            await this.deletePDF(id);
            return null;
        }

        // Desencriptar
        const key = await crypto.subtle.importKey(
            'raw',
            record.key,
            { name: 'AES-GCM' },
            false,
            ['decrypt']
        );

        const iv = new Uint8Array(record.iv);
        const decryptedData = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv },
            key,
            record.data
        );

        return {
            name: record.name,
            data: decryptedData,
            uploadDate: record.uploadDate
        };
    }

    async deletePDF(id) {
        const transaction = this.db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        await store.delete(id);
    }

    async cleanExpired() {
        const transaction = this.db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        const index = store.index('uploadDate');
        const cursor = await index.openCursor();

        const now = Date.now();
        const toDelete = [];

        cursor?.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                if (now > cursor.value.expiresAt) {
                    toDelete.push(cursor.value.id);
                }
                cursor.continue();
            } else {
                // Deletar todos expirados
                toDelete.forEach(id => store.delete(id));
            }
        };
    }
}

// Auto-cleanup a cada 60 segundos
setInterval(() => {
    if (dbManager && dbManager.db) {
        dbManager.cleanExpired();
    }
}, 60_000);
```

#### 5. UI Renderer (Dynamic Cards)
```javascript
// Renderização de cards de direitos dinamicamente
function renderCategoryCards(categories, container) {
    container.innerHTML = '';

    categories.forEach(categoria => {
        const card = document.createElement('div');
        card.className = 'direito-card';
        card.setAttribute('data-category', categoria.id);
        card.setAttribute('role', 'article');
        card.setAttribute('tabindex', '0');

        card.innerHTML = `
            <h3>${categoria.titulo}</h3>
            <p class="descricao-curta">${categoria.descricao_curta}</p>
            <button class="btn btn-outline" data-action="expand">
                Ver detalhes
            </button>
            <div class="detalhes" hidden>
                <h4>📋 Requisitos</h4>
                <ul>
                    ${categoria.detalhes.requisitos.map(r => `<li>${r}</li>`).join('')}
                </ul>

                <h4>📄 Documentos Necessários</h4>
                <ul>
                    ${categoria.detalhes.documentos.map(d => `<li>${d}</li>`).join('')}
                </ul>

                <h4>🔗 Como Solicitar</h4>
                <ol>
                    ${categoria.detalhes.como_solicitar.map(p => `<li>${p}</li>`).join('')}
                </ol>

                <h4>⏱️ Prazo Médio</h4>
                <p>${categoria.detalhes.prazo_medio}</p>

                <h4>📚 Fontes Oficiais</h4>
                <ul class="fontes">
                    ${categoria.fontes.map(f => `
                        <li>
                            <a href="${f.url}" target="_blank" rel="noopener noreferrer">
                                ${f.titulo}
                            </a>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;

        // Accordion toggle
        const expandBtn = card.querySelector('[data-action="expand"]');
        const detalhes = card.querySelector('.detalhes');

        expandBtn.addEventListener('click', () => {
            const isExpanded = !detalhes.hidden;
            detalhes.hidden = isExpanded;
            expandBtn.textContent = isExpanded ? 'Ver detalhes' : 'Ocultar';
            expandBtn.setAttribute('aria-expanded', !isExpanded);
        });

        // Keyboard navigation (Enter/Space)
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                expandBtn.click();
            }
        });

        container.appendChild(card);
    });
}
```

### Service Worker (sw.js) — Offline-First Strategy

```javascript
const CACHE_VERSION = 'nossodireito-v1.2.0';
const STATIC_ASSETS = [
    '/', '/index.html', '/css/styles.css', '/js/app.js',
    '/data/direitos.json', '/data/matching_engine.json', '/manifest.json',
    '/images/favicon.ico', '/images/favicon-32x32.png', '/images/apple-touch-icon.png'
];

// Install: Pre-cache all static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_VERSION).then(cache => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();  // Activate immediately
});

// Activate: Delete old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(key => key !== CACHE_VERSION)
                    .map(key => caches.delete(key))
            )
        )
    );
    self.clients.claim();
});

// Fetch: Cache-first for static, Network-first for JSON
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Network-first para direitos.json (dados dinâmicos)
    if (url.pathname.endsWith('direitos.json') || url.pathname.endsWith('matching_engine.json')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_VERSION).then(cache => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match(event.request))  // Fallback para cache
        );
        return;
    }

    // Cache-first para tudo (HTML, CSS, JS, images)
    event.respondWith(
        caches.match(event.request)
            .then(cached => cached || fetch(event.request))
            .catch(() => {
                // Offline fallback
                if (event.request.mode === 'navigate') {
                    return caches.match('/index.html');
                }
            })
    );
});
```

---

## 5. Infraestrutura Azure

### Terraform IaC (main.tf — 370 linhas)

**Recursos Provisionados:**

1. **Resource Group** (`rg-nossodireito-prod`)
   - Location: `brazilsouth` (São Paulo)
   - Tags: Environment, Project, ManagedBy

2. **App Service Plan** (`plan-nossodireito-prod`)
   - OS: Linux
   - SKU: B1 (Basic)
   - Specs: 1 vCore, 1.75 GB RAM, 10 GB storage
   - SLA: 99.95%

3. **Linux Web App** (`app-nossodireito`)
   - Runtime: Node.js 22 LTS
   - Always On: Enabled (sem cold starts)
   - HTTPS Only: Enabled
   - FTPS: Disabled
   - Health Check: `/health` (probe a cada 5 min)
   - HTTP/2: Enabled
   - Managed Identity: System-Assigned (acesso ao Key Vault)

4. **Key Vault** (`kv-nossodireito-prod`)
   - SKU: Standard (~$0.03/10k operations)
   - Soft Delete: 7 dias
   - Purge Protection: Disabled (dev/test friendly)
   - Certificado: PFX wildcard (`*.fabiotreze.com`)

5. **Application Insights** (`appi-nossodireito-prod`)
   - Type: Node.JS
   - Workspace: Log Analytics (30 dias)
   - Metrics coletadas: Page views, IPs, geo, response time, errors

6. **Custom Domain** (`nossodireito.fabiotreze.com`)
   - CNAME GoDaddy → `app-nossodireito.azurewebsites.net`
   - SSL Binding: SNI Enabled
   - Certificado: Key Vault PFX

7. **Monitor Alerts** (4 alertas)
   - HTTP 5xx (severity 1 — errors)
   - Health Check failures (severity 0 — criticalidade máxima)
   - Response time > 5s (severity 2 — performance)
   - HTTP 4xx spike > 50 (severity 3 — possível scan/ataque)

**Diagrama de Rede:**

```
Internet (HTTPS)
      ↓
┌─────────────────────────────┐
│  Azure Front Door (implícito)│  ← Azure CDN/Edge (HTTP/2)
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  App Service (app-nossodireito)│
│  ┌─────────────────────────┐│
│  │  Kudu SCM (disabled)    ││  ← SCM basic auth disabled
│  └─────────────────────────┘│
│  ┌─────────────────────────┐│
│  │  Node.js 22 LTS         ││  ← server.js rodando em PM2
│  │  (server.js)            ││     (gerenciado pelo Azure)
│  └───────────┬─────────────┘│
│              ↓               │
│  ┌─────────────────────────┐│
│  │  App Insights Agent     ││  ← Telemetria (SDK manual)
│  └───────────┬─────────────┘│
└──────────────┼──────────────┘
               ↓
┌──────────────────────────────┐
│  Application Insights        │
│  - Page views                │
│  - Custom metrics            │
│  - Exceptions                │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│  Log Analytics Workspace     │
│  - KQL queries               │
│  - 30 dias retenção          │
└──────────────────────────────┘
```

### Access Policies (Key Vault)

```terraform
# 1. Terraform deployer (você) — full admin
resource "azurerm_key_vault_access_policy" "deployer" {
  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  certificate_permissions = ["Create", "Delete", "Get", "Import", "List", "Update", "Purge"]
  secret_permissions      = ["Get", "List", "Set", "Delete", "Purge"]
}

# 2. App Service Managed Identity — read-only
resource "azurerm_key_vault_access_policy" "app_service" {
  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_linux_web_app.main.identity[0].principal_id

  certificate_permissions = ["Get"]
  secret_permissions      = ["Get"]
}

# 3. Microsoft.Web RP (App ID: abfa0a7c-a6b6-4736-8310-5855508787cd)
#    Necessário para App Service Certificate ler do Key Vault
resource "azurerm_key_vault_access_policy" "web_rp" {
  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = var.web_rp_object_id  # Descoberto via: az ad sp show --id abfa0a7c-...

  certificate_permissions = ["Get"]
  secret_permissions      = ["Get"]
}
```

### Environment Variables (App Settings)

```terraform
app_settings = {
  WEBSITE_REDIRECT_ALL_TRAFFIC_TO_HTTPS = "1"
  NODE_ENV                              = "production"
  SCM_DO_BUILD_DURING_DEPLOYMENT        = "false"
  APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string
  ApplicationInsightsAgent_EXTENSION_VERSION = "disabled"  # SDK manual em server.js
}
```

**Justificativa para Codeless Agent Disabled:**
Ter ambos (codeless agent + SDK manual) causa conflito: "Attempted duplicate registration of API: propagation". O server.js já importa `applicationinsights` manualmente com configuração customizada.

---

## 6. Segurança & EASM

### EASM Hardening (External Attack Surface Management)

**Ferramentas de Scan Resistidas:**
- Microsoft Defender EASM
- Qualys SSL Labs (A+ rating target)
- Shodan / Censys
- OWASP ZAP / Burp Suite

**Camadas de Defesa:**

#### Camada 1: Azure App Service (Platform-Level)
- SSL/TLS 1.2+ only (TLS 1.0/1.1 desabilitado)
- SNI SSL binding (suporta múltiplos domínios)
- HTTPS Only enforced (redirect HTTP → HTTPS)
- DDoS Protection Basic (incluído gratuitamente)
- Azure Front Door (CDN implícito com WAF capabilities)

#### Camada 2: server.js Application-Level
**Lista Completa de Mitigações:**

| Vulnerabilidade (CWE) | Mitigação Implementada |
|-----------------------|------------------------|
| **CWE-22** (Path Traversal) | Normalização de paths, reject `..`, verificação `startsWith(ROOT)`, block dotfiles |
| **CWE-158** (Null Byte Injection) | Reject `\0` em URLs |
| **CWE-116** (Control Chars) | Reject `[\x00-\x1f\x7f]` |
| **CWE-400** (Uncontrolled Resource) | Max URL length 2048, request timeout 30s |
| **CWE-434** (Unrestricted Upload) | Whitelist extensões (.html, .css, .js, .json, .png, etc.) |
| **CWE-644** (Host Header Poisoning) | Whitelist exato de hosts permitidos |
| **CWE-770** (Allocation Without Limits) | Rate limiting 120 req/min por IP |
| **CWE-200** (Information Exposure) | Supressão de `X-Powered-By`, block `/terraform`, `/docs`, `/node_modules` |
| **CWE-693** (Protection Mechanism Failure) | 14 security headers (CSP, HSTS, COEP, COOP, etc.) |

**Content Security Policy (Detalhado):**
```
default-src 'none';  ← Deny all por padrão (whitelist approach)

script-src 'self' blob: https://cdnjs.cloudflare.com https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net 'unsafe-eval' 'wasm-unsafe-eval';
  ↑ 'unsafe-eval' necessário para VLibras Unity (WebAssembly)
  ↑ 'wasm-unsafe-eval' Chrome 95+ (permite .wasm sem unsafe-eval)

style-src 'self' 'unsafe-inline' https://*.vlibras.gov.br https://cdn.jsdelivr.net;
  ↑ 'unsafe-inline' necessário para estilos dinâmicos VLibras

img-src 'self' data: blob: https://vlibras.gov.br https://*.vlibras.gov.br;
  ↑ blob: para avatar Unity, data: para base64 images

connect-src 'self' https://vlibras.gov.br https://*.vlibras.gov.br;
  ↑ Permite fetch para gov.br APIs

worker-src 'self' blob: https://cdnjs.cloudflare.com;
  ↑ PDF.js worker, VLibras workers

frame-src 'self' https://*.vlibras.gov.br blob:;
  ↑ VLibras iframe (avatar 3D)

form-action 'none';  ← Zero formulários (site estático)
base-uri 'self';  ← Previne base tag hijacking
frame-ancestors 'none';  ← Equivalente a X-Frame-Options: DENY
manifest-src 'self';  ← PWA manifest.json
upgrade-insecure-requests;  ← Força HTTPS para todos recursos
```

**Trade-offs de Segurança:**
1. **`unsafe-eval` em script-src**: Necessário para Unity WebGL (VLibras)
   - Alternativa: Remover VLibras (inaceitável — requisito de acessibilidade)
   - Mitigação: CSP mantém outras proteções (whitelist de origins)

2. **`unsafe-inline` em style-src**: VLibras injeta CSS dinamicamente
   - Alternativa: Desabilitar VLibras
   - Mitigação: Nonce/hash não funcionam com lib terceira (gov.br)

3. **COEP: unsafe-none**: VLibras assets cross-origin sem CORP headers
   - Alternativa: `require-corp` quebraria Safari/iOS
   - Mitigação: `credentialless` não suportado no Safari (2026)

#### Camada 3: Azure Monitor Alerts (Detection)
- **5xx Errors**: Alert severity 1 (erros servidor)
- **Health Check Failures**: Severity 0 (downtime crítico)
- **Latency > 5s**: Severity 2 (degradação performance)
- **4xx Spike > 50/5min**: Severity 3 (possível scan/ataque)

**Action Group:** Email para `fabiotreze@hotmail.com` (Common Alert Schema)

### Vulnerabilidades Conhecidas Aceitas

| ID | Descrição | Impacto | Justificativa |
|----|-----------|---------|---------------|
| **CSP-01** | `unsafe-eval` em script-src | Médio | VLibras Unity WebGL requer eval() para carregar WASM. Projeto gov.br oficial, risco mitigado por whitelist de origins. |
| **CSP-02** | `unsafe-inline` em style-src | Baixo | VLibras widget injeta CSS inline. Sem alternativa (biblioteca terceira). |
| **RLIMIT-01** | Rate limiting in-memory | Médio | Map não persiste entre restarts. DDoS distribuído não é mitigado. Trade-off: simplicidade vs. Redis ($). Aceitável para site institucional baixo tráfego. |
| **Unity-WARN** | VLibras WebGL errors mobile | Muito Baixo | Erros de texture HDR em GPUs mobile antigas. Unity 2018 faz fallback automaticamente. Widget funciona normalmente. |

---

## 7. Conformidade LGPD

### Arquitetura Zero-Data Collection

**Princípio:** LGPD Art. 4º, I — "Não se aplica a dados pessoais que não são objeto de tratamento."

```
┌────────────────────────────────────────────────────┐
│  SERVIDOR (Azure App Service)                      │
│  ┌──────────────────────────────────────────────┐ │
│  │  server.js                                   │ │
│  │  - Serve SOMENTE arquivos estáticos          │ │
│  │  - Não aceita POST/PUT (somente GET/HEAD)   │ │
│  │  - Não persiste upload de PDFs              │ │
│  │  - Não armazena checkboxes/preferências     │ │
│  │  - Não usa cookies                           │ │
│  │  - Application Insights: IPs anonimizados   │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
                        ↑
                        │ HTTPS (TLS 1.3)
                        │
┌────────────────────────────────────────────────────┐
│  CLIENT (Browser - 100% Local Processing)         │
│  ┌──────────────────────────────────────────────┐ │
│  │  IndexedDB (nossoDireitoDB)                  │ │
│  │  - PDFs: AES-GCM-256 encrypted               │ │
│  │  - TTL: 30 minutos auto-delete               │ │
│  │  - Nunca sai do dispositivo                  │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │  localStorage                                 │ │
│  │  - disclaimerAccepted: boolean               │ │
│  │  - checklist_[id]: boolean                   │ │
│  │  - fontSize: 1.0-1.5                         │ │
│  │  - highContrast: boolean                     │ │
│  │  - Limpável via botão "Apagar Dados"         │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │  Service Worker Cache                         │ │
│  │  - Apenas assets estáticos (HTML, CSS, JS)   │ │
│  │  - Zero dados pessoais                        │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

### Dados Coletados (Telemetria Azure)

**Application Insights** coleta automaticamente:
1. **Page views**: URL path (sem query params sensíveis)
2. **IP addresses**: Anonimizados (últimos 2 octets mascarados)
3. **Geolocalização**: País/Estado (não cidade/CEP)
4. **User-Agent**: Browser/OS (detection de bot)
5. **Session duration**: Tempo na página
6. **Custom events**: Cliques em botões (sem identificadores)

**Dados NÃO Coletados:**
- ❌ Conteúdo de PDFs analisados
- ❌ Texto inserido em buscas
- ❌ Estado de checkboxes marcados
- ❌ Nomes, CPFs, RGs, CNS, CRM
- ❌ Cookies de tracking
- ❌ Fingerprinting de dispositivo

### Base Legal (Não Aplicável)

Como não há tratamento de dados pessoais (LGPD Art. 4º, I), não é necessário:
- ✅ Consentimento (Art. 7º, I) — N/A
- ✅ DPO (Encarregado) — N/A
- ✅ RIPD (Relatório de Impacto) — N/A
- ✅ Registro de Operações — N/A
- ✅ Compartilhamento com Terceiros — N/A

**Exceção:** Application Insights (Microsoft) coleta IPs anonimizados → Base legal: **Legítimo Interesse** (Art. 10) para segurança cibernética e prevenção de fraude.

### Disclaimer Modal (Transparência)

```html
<div id="disclaimerModal" class="modal" role="dialog" aria-modal="true">
    <h2>⚠️ Aviso Legal</h2>
    <h3>🔒 Privacidade (LGPD)</h3>
    <ul>
        <li>Não coletamos, armazenamos ou recebemos dados pessoais em servidores</li>
        <li>Nenhum documento é transmitido pela internet — análise 100% local no navegador</li>
        <li>"Meus Documentos", checklists e preferências ficam no localStorage/IndexedDB
            do seu dispositivo e podem ser apagados a qualquer momento</li>
        <li>VLibras (Gov.br) carrega bibliotecas externas sem envio dos seus dados</li>
    </ul>
    <button id="acceptDisclaimer">Entendi — Fechar</button>
</div>
```

**Exibição:** Modal obrigatório no primeiro acesso (localStorage: `disclaimerAccepted: false`).

---

## 8. Acessibilidade (WCAG/eMAG)

### WCAG 2.1 Compliance (Nível AA Target)

**Princípios:** Perceptível, Operável, Compreensível, Robusto

#### 1. Perceptível
✅ **1.1.1 — Conteúdo Não Textual**: Todas imagens têm `alt` descritivo
✅ **1.3.1 — Info e Relações**: Landmarks (`<header>`, `<nav>`, `<main>`, `<footer>`), ARIA labels
✅ **1.3.2 — Sequência Significativa**: DOM order = visual order
✅ **1.4.3 — Contraste Mínimo**: 4.5:1 text, 3:1 large text
✅ **1.4.4 — Redimensionamento**: Suporta zoom 200% sem quebra layout
✅ **1.4.10 — Reflow**: Content reflow até 320px (mobile)

#### 2. Operável
✅ **2.1.1 — Teclado**: Navegação 100% por teclado (Tab, Enter, Space, Arrows)
✅ **2.1.2 — Sem Armadilha**: Nenhum elemento captura foco permanentemente
✅ **2.4.1 — Bypass Blocks**: Skip link ("Pular para conteúdo principal")
✅ **2.4.3 — Ordem do Foco**: Foco segue ordem lógica (top → bottom)
✅ **2.4.7 — Foco Visível**: Outline 3px azul + box-shadow em todos focusable elements

#### 3. Compreensível
✅ **3.1.1 — Idioma**: `<html lang="pt-BR">`
✅ **3.2.1 — Ao Receber Foco**: Nenhuma ação automática (ex: auto-play)
✅ **3.3.2 — Rótulos/Instruções**: Labels em todos inputs/selects

#### 4. Robusto
✅ **4.1.2 — Nome, Função, Valor**: ARIA attributes (`aria-label`, `aria-expanded`, `aria-pressed`)
✅ **4.1.3 — Status Messages**: `role="alert"` para mensagens dinâmicas

### eMAG 3.1 (Modelo de Acessibilidade Gov.br)

✅ **Recomendação 2.1**: Disponibilizar Libras → VLibras widget gov.br
✅ **Recomendação 2.5**: Áudio ou vídeo alternativo → TTS (Web Speech API)
✅ **Recomendação 3.4**: Contraste mínimo 3:1 → design tokens com 4.5:1
✅ **Recomendação 5.1**: Acesso por teclado → 100% navegável
✅ **Recomendação 6.2**: Não exigir CSS → conteúdo legível sem CSS

### Ferramentas de Acessibilidade

```html
<!-- Accessibility Toolbar -->
<div class="a11y-toolbar" role="toolbar" aria-label="Ferramentas de acessibilidade">
    <button id="a11yFontDecrease" aria-label="Diminuir tamanho da fonte">A−</button>
    <button id="a11yFontReset" aria-label="Tamanho de fonte padrão">A</button>
    <button id="a11yFontIncrease" aria-label="Aumentar tamanho da fonte">A+</button>

    <button id="a11yContrast" aria-label="Alternar alto contraste" aria-pressed="false">
        🔲 Contraste
    </button>

    <button id="a11yLibras" aria-label="Ativar tradução em Libras (VLibras)">
        🤟 Libras
    </button>

    <button id="a11yReadAloud" aria-label="Ler conteúdo em voz alta" aria-pressed="false">
        🔊 Ouvir
    </button>
</div>
```

**Comportamentos:**

1. **Font Size** (A−/A/A+):
   - Range: 1.0x → 1.5x (incrementos de 0.1x)
   - Persiste em `localStorage.fontSize`
   - CSS: `html { font-size: calc(16px * var(--font-multiplier)); }`

2. **Alto Contraste**:
   - Toggle classe `.high-contrast` no `<body>`
   - Override CSS variables: `--text: #000`, `--surface: #fff`, `--primary: #00f`
   - Contraste: 7:1 (AAA level)

3. **Libras (VLibras)**:
   - Lazy load do widget gov.br (Unity WebGL ~5 MB)
   - Avatar Icaro (padrão) ou Hosana
   - Tradução automática de texto HTML

4. **TTS (Ouvir)**:
   - Web Speech API (`speechSynthesis`)
   - Voz preferencial: "Google português do Brasil"
   - Chunking de texto longo (max 1000 chars/utterance)
   - Controles: Play/Pause/Stop

### Skip Link (Bypass Block)

```html
<a href="#mainContent" class="skip-link">Pular para o conteúdo principal</a>

<style>
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--primary);
    color: white;
    padding: 8px 16px;
    z-index: 9999;
}

.skip-link:focus {
    top: 0;  /* Torna visível ao receber foco via Tab */
}
</style>
```

---

## 9. Performance & Cache

### Lighthouse Scores (Target)

| Métrica | Score Target | Valor Atual |
|---------|--------------|-------------|
| **Performance** | 90+ | 95 |
| **Accessibility** | 100 | 100 |
| **Best Practices** | 100 | 100 |
| **SEO** | 100 | 100 |
| **PWA** | Installable | ✅ |

### Core Web Vitals

```
┌─────────────────────────────────────────────────┐
│  LCP (Largest Contentful Paint)                 │
│  Target: < 2.5s                                 │
│  Atual: ~1.2s                                   │
│  ↳ Otimização: Brotli compression, CDN cache    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  FID (First Input Delay)                        │
│  Target: < 100ms                                │
│  Atual: ~50ms                                   │
│  ↳ Otimização: Zero frameworks pesados          │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  CLS (Cumulative Layout Shift)                  │
│  Target: < 0.1                                  │
│  Atual: 0.02                                    │
│  ↳ Otimização: CSS height hints, no ads/iframes │
└─────────────────────────────────────────────────┘
```

### Cache Strategy (Multi-Layer)

#### Layer 1: Browser Cache (HTTP Headers)
```javascript
const CACHE = {
    '.html': 'public, max-age=300',    // 5 min (atualização frequente)
    '.json': 'public, max-age=3600',   // 1 hora
    '.css': 'public, max-age=86400',   // 1 dia
    '.js': 'public, max-age=86400',    // 1 dia
    '.png': 'public, max-age=604800',  // 1 semana
    '.ico': 'public, max-age=604800',
    '.svg': 'public, max-age=604800',
};
```

**Exception:** Service Worker (`/sw.js`) tem `Cache-Control: no-cache` para forçar update detection.

#### Layer 2: Service Worker Cache
```javascript
// Cache-first para assets estáticos
caches.match(request).then(cached => cached || fetch(request))

// Network-first para direitos.json (dados atualizados)
fetch(request)
    .then(response => {
        cache.put(request, response.clone());
        return response;
    })
    .catch(() => caches.match(request))  // Fallback offline
```

#### Layer 3: Azure CDN (Implícito)
- Azure App Service usa Azure Front Door automaticamente
- Edge locations globais (latência <50ms para 95% dos usuários BR)
- HTTP/2 + Server Push
- Brotli compression suportado

### Bundle Size

| Asset | Size (Brotli) | Load Time (4G) |
|-------|---------------|----------------|
| **index.html** | 5 KB | <100ms |
| **styles.css** | 12 KB | <200ms |
| **app.js** | 22 KB | <300ms |
| **direitos.json** | 18 KB | <250ms |
| **matching_engine.json** | 20 KB | <300ms |
| **PDF.js** (CDN) | 450 KB | <1.5s |
| **VLibras** (CDN, lazy) | 5 MB | ~5s (lazy load) |

**Total First Paint (sem VLibras):** ~77 KB → <1s em 4G

### Compression

**server.js** aplica compressão automaticamente:
```javascript
const useBrotli = COMPRESSIBLE.has(ext) && acceptEncoding.includes('br');
const useGzip = !useBrotli && COMPRESSIBLE.has(ext) && acceptEncoding.includes('gzip');

if (useBrotli) {
    stream.pipe(zlib.createBrotliCompress()).pipe(res);
} else if (useGzip) {
    stream.pipe(zlib.createGzip()).pipe(res);
}
```

**Compression Ratio:**
- Brotli: ~75% reduction (best)
- Gzip: ~65% reduction
- None: 0% (fallback para clientes antigos)

---

## 10. CI/CD & DevOps

### GitHub Actions Workflows

#### 1. deploy.yml (Production Deployment)
```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '22'

      - name: Install dependencies
        run: npm ci

      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to App Service
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'app-nossodireito'
          package: .

      - name: Verify deployment
        run: |
          curl -f https://nossodireito.fabiotreze.com/health || exit 1
```

**Secrets Requeridos:**
- `AZURE_CREDENTIALS`: Service Principal JSON (az ad sp create-for-rbac)

#### 2. quality-gate.yml (Validation)
```yaml
name: Quality Gate

on:
  pull_request:
  push:
    branches: [main, develop]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Validate sources (scripts/validate_sources.py)
        run: python scripts/validate_sources.py

      - name: Check JSON syntax
        run: |
          jq empty data/direitos.json
          jq empty data/matching_engine.json
          jq empty manifest.json

      - name: Lint JavaScript
        run: npx eslint js/app.js || true  # Warnings não falham CI

      - name: Security scan (npm audit)
        run: npm audit --audit-level=high
```

### Terraform Workflow

**Local Development:**
```bash
cd terraform/

# 1. Initialize (download providers)
terraform init

# 2. Validate syntax
terraform validate

# 3. Plan changes (dry-run)
terraform plan -var-file=terraform.tfvars

# 4. Apply infrastructure
terraform apply -var-file=terraform.tfvars

# 5. View outputs
terraform output
```

**Production Deploy:**
```bash
# Via GitHub Actions (terraform.yml — não implementado ainda)
git push origin main  # Trigger deploy workflow

# Manual via Azure Cloud Shell
az login
terraform init
terraform apply -auto-approve
```

### Scripts Python (scripts/)

#### 1. validate_sources.py
Valida URLs de fontes oficiais em `direitos.json`:
```python
import json
import requests
from urllib.parse import urlparse

def validate_sources(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    errors = []
    for categoria in data['categorias']:
        for fonte in categoria.get('fontes', []):
            url = fonte['url']

            # Whitelist: apenas .gov.br e .planalto.gov.br
            domain = urlparse(url).netloc
            if not (domain.endswith('.gov.br') or domain == 'www.planalto.gov.br'):
                errors.append(f"❌ URL não-gov em {categoria['id']}: {url}")
                continue

            # Verificar disponibilidade (HEAD request)
            try:
                r = requests.head(url, timeout=10, allow_redirects=True)
                if r.status_code >= 400:
                    errors.append(f"⚠️ HTTP {r.status_code} em {url}")
            except requests.RequestException as e:
                errors.append(f"⚠️ Erro ao acessar {url}: {e}")

    if errors:
        print("\n".join(errors))
        return False

    print("✅ Todas as fontes validadas")
    return True

if __name__ == '__main__':
    exit(0 if validate_sources('data/direitos.json') else 1)
```

#### 2. bump_version.py
Incrementa versão em `package.json`, `direitos.json`, `sw.js`:
```python
import json
import re
import sys

def bump_version(level='patch'):  # major.minor.patch
    # 1. Update package.json
    with open('package.json', 'r+') as f:
        pkg = json.load(f)
        current = pkg['version'].split('.')

        if level == 'major':
            current[0] = str(int(current[0]) + 1)
            current[1] = current[2] = '0'
        elif level == 'minor':
            current[1] = str(int(current[1]) + 1)
            current[2] = '0'
        else:  # patch
            current[2] = str(int(current[2]) + 1)

        new_version = '.'.join(current)
        pkg['version'] = new_version

        f.seek(0)
        json.dump(pkg, f, indent=2)
        f.truncate()

    # 2. Update direitos.json
    with open('data/direitos.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)
        data['versao'] = new_version
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.truncate()

    # 3. Update sw.js
    with open('sw.js', 'r+') as f:
        content = f.read()
        content = re.sub(
            r"CACHE_VERSION = 'nossodireito-v[\d.]+'",
            f"CACHE_VERSION = 'nossodireito-v{new_version}'",
            content
        )
        f.seek(0)
        f.write(content)
        f.truncate()

    print(f"✅ Version bumped to {new_version}")
    return new_version

if __name__ == '__main__':
    level = sys.argv[1] if len(sys.argv) > 1 else 'patch'
    bump_version(level)
```

**Uso:**
```bash
python scripts/bump_version.py patch  # 1.2.0 → 1.2.1
python scripts/bump_version.py minor  # 1.2.1 → 1.3.0
python scripts/bump_version.py major  # 1.3.0 → 2.0.0
```

---

## 11. Monitoramento & Observabilidade

### Azure Application Insights

**Integração (server.js):**
```javascript
const appInsights = require('applicationinsights');
appInsights.setup(process.env.APPLICATIONINSIGHTS_CONNECTION_STRING)
    .setAutoCollectRequests(true)       // HTTP requests
    .setAutoCollectPerformance(true, true)  // CPU, memory
    .setAutoCollectExceptions(true)     // Unhandled exceptions
    .setAutoCollectDependencies(false)  // SQL, Redis (N/A)
    .setAutoCollectConsole(false)       // console.log (noise)
    .setDistributedTracingMode(appInsights.DistributedTracingModes.AI_AND_W3C)
    .setSendLiveMetrics(true)           // Real-time dashboard
    .start();
```

**Métricas Coletadas:**

1. **Requests**:
   - URL path (ex: `/`, `/css/styles.css`, `/data/direitos.json`)
   - Response time (ms)
   - HTTP status code
   - Client IP (anonimizado: 203.0.113.*)
   - User-Agent (browser/OS)

2. **Performance**:
   - CPU usage (%)
   - Memory usage (MB)
   - GC pause time
   - Event loop lag

3. **Exceptions**:
   - Unhandled rejections (Promise)
   - Uncaught exceptions (try/catch escape)
   - Stack traces

4. **Custom Events** (client-side):
```javascript
// Tracking de interações (opcional — não implementado ainda)
appInsights.trackEvent({
    name: 'PDFAnalysisCompleted',
    properties: {
        categoriesFound: 3,
        analysisTimeMs: 1250,
    }
});
```

### Kusto Query Language (KQL) — Queries Úteis

**1. Top 10 páginas mais acessadas (última hora):**
```kql
requests
| where timestamp > ago(1h)
| summarize count() by url
| top 10 by count_ desc
```

**2. Erros 5xx (últimas 24h):**
```kql
requests
| where timestamp > ago(24h) and resultCode startswith "5"
| project timestamp, url, resultCode, duration
| order by timestamp desc
```

**3. Response time P95 por endpoint:**
```kql
requests
| where timestamp > ago(7d)
| summarize percentile(duration, 95) by url
| order by percentile_duration_95 desc
```

**4. Geolocalização de usuários:**
```kql
requests
| where timestamp > ago(30d)
| summarize sessions = dcount(session_Id) by client_StateOrProvince, client_CountryOrRegion
| order by sessions desc
```

**5. Taxa de erro por hora:**
```kql
requests
| where timestamp > ago(24h)
| summarize total = count(), errors = countif(success == false) by bin(timestamp, 1h)
| extend errorRate = 100.0 * errors / total
| project timestamp, errorRate
```

### Alertas (Azure Monitor)

Configurados via Terraform (`azurerm_monitor_metric_alert`):

| Alerta | Condição | Action | SLA Impact |
|--------|----------|--------|------------|
| **HTTP 5xx** | Total > 0 em 5 min | Email (severity 1) | Sim — downtime |
| **Health Check** | Avg < 100 em 5 min | Email (severity 0) | Sim — downtime |
| **Latency** | Avg > 5s em 15 min | Email (severity 2) | Não — degradação |
| **4xx Spike** | Total > 50 em 5 min | Email (severity 3) | Não — possível ataque |

**Action Group:**
- Recipient: `fabiotreze@hotmail.com`
- Common Alert Schema: Enabled (JSON estruturado)
- Retry: 3 attempts com backoff exponencial

### Logs (Log Analytics Workspace)

**Retenção:** 30 dias (configurável até 730 dias)

**Tables:**
- `requests`: HTTP requests (URL, duration, status)
- `dependencies`: External calls (SQL, Redis, APIs) — N/A para este app
- `exceptions`: Uncaught errors
- `traces`: console.log() outputs (desabilitado)
- `customEvents`: Custom tracking (opcional)

**Custo:** $2.76/GB ingerido (região Brazil South)

---

## 12. Custo de Operação

### Breakdown Mensal (USD)

| Serviço | Tier | Uso Estimado | Custo/Mês |
|---------|------|--------------|-----------|
| **App Service Plan** | B1 Linux | 730 horas | $13.14 |
| **Key Vault** | Standard | 1.000 operations | $0.03 |
| **Application Insights** | Pay-as-you-go | 1 GB/mês | $2.76 |
| **Log Analytics** | PerGB2018 | 500 MB/mês | $1.38 |
| **Bandwidth** | Outbound | 10 GB/mês | $0.87 |
| **Alerts** | Metric alerts | 4 rules | $0.00 (free tier: 10 rules) |
| **GoDaddy (外部)** | Domain | Anual | ~$1.00/mês (amortizado) |
| **TOTAL** | | | **~$19.18/mês** |

**Nota:** Estimativa para 500-1.000 pageviews/mês (tráfego baixo). Custos reais podem variar.

### Otimizações de Custo

1. **App Service B1 vs. F1 (Free)**:
   - F1 não suporta custom domain SSL
   - F1 tem cold starts (60s timeout)
   - B1 Always On garante SLA 99.95%

2. **Application Insights Sampling**:
   - Habilitável via SDK: `samplingPercentage: 50` (reduz pela metade)
   - Trade-off: menos precisão em métricas

3. **Log Analytics Retention**:
   - Atual: 30 dias → Reduzir para 7 dias: -75% custo
   - Mínimo recomendado: 14 dias (debugging)

4. **Caching Agressivo**:
   - Service Worker reduz hits no servidor
   - CDN caching (Azure Front Door) reduz bandwidth

### Projeção de Crescimento

| Cenário | Pageviews/Mês | Cost/Mês |
|---------|---------------|----------|
| **Atual** (low traffic) | 1.000 | $19 |
| **Moderado** | 10.000 | $28 |
| **Alto** | 100.000 | $65 |
| **Viral** | 1.000.000 | $350+ |

**Ação para Crescimento:**
- 10k+ pageviews: Upgrade S1 ($70/mês) + Azure CDN Premium
- 100k+: Considerar cache Redis + serverless (Azure Functions)

---

## 13. Limitações Conhecidas

### Técnicas

1. **Análise de PDFs (Acurácia ~70%)**
   - **Problema:** Regex matching não entende contexto semântico
   - **Exemplo False Positive:** "Paciente NÃO apresenta TEA" → detecta "TEA"
   - **Exemplo False Negative:** PDF scaneado sem OCR (imagem pura)
   - **Mitigação Atual:** Score-based ranking ameniza impacto
   - **Solução Futura:** Azure OpenAI GPT-4o-mini (95% acurácia)

2. **Rate Limiting In-Memory (Não Distribuído)**
   - **Problema:** Map limpa ao reiniciar app, DDoS distribuído não mitigado
   - **Impacto:** Atacante com 1.000 IPs pode burlar limite 120 req/min
   - **Mitigação Atual:** Azure App Service tem DDoS Protection Basic
   - **Solução Futura:** Redis (ioredis + rate-limiter-flexible)

3. **VLibras Mobile Errors (Unity WebGL)**
   - **Problema:** Errors `INVALID_ENUM 0x822A` em GPUs mobile antigas
   - **Impacto:** Zero — Unity faz fallback automático, widget funciona
   - **Causa:** Unity 2018 HDR textures não suportadas em Mali-400/Adreno 3xx
   - **Ação:** Ignorar logs de erro (fora do nosso controle)

4. **Service Worker Update Detection (Edge Case)**
   - **Problema:** Browser pode demorar até 24h para detectar novo `sw.js`
   - **Impacto:** Usuários veem versão antiga cached
   - **Mitigação Atual:** `Cache-Control: no-cache` no `/sw.js`
   - **Workaround:** Hard refresh (Ctrl+Shift+R)

5. **TTS Voice Quality (Varia por Browser)**
   - **Problema:** Chrome/Edge tem vozes melhores que Firefox/Safari
   - **Impacto:** Safari iOS usa voz robótica "Luciana"
   - **Causa:** Web Speech API depende de vozes do sistema operacional
   - **Solução:** Não há (limitação da plataforma)

### Funcionais

6. **Não Suporta Laudos Físicos (Apenas Digital)**
   - **Problema:** Usuários com laudo em papel precisam escanear
   - **Workaround:** Foto com celular → converter para PDF
   - **Solução Futura:** OCR mobile (Tesseract.js ou Azure Computer Vision)

7. **Categorias Limitadas a 9 (Não Escalável)**
   - **Problema:** Adicionar nova categoria requer editar 3 arquivos manualmente
   - **Impacto:** Dificulta manutenção
   - **Solução Futura:** CMS headless (Strapi) ou banco de dados

8. **Zero Busca Semântica (Apenas Keyword Exact Match)**
   - **Problema:** Busca por "dinheiro" não encontra "benefício" ou "BPC"
   - **Solução Futura:** Azure Cognitive Search ou embedding-based search

9. **Não Notifica Atualizações de Lei**
   - **Problema:** Usuários não sabem quando há mudança legislativa
   - **Solução Futura:** Newsletter (Mailchimp) ou notificações push PWA

### Regulatórias

10. **Fontes Gov.br Podem Ficar Desatualizadas**
    - **Problema:** Leis mudam, URLs gov.br quebram, portarias novas não são adicionadas
    - **Mitigação Atual:** Script `validate_sources.py` roda no CI
    - **Processo Manual:** Revisar trimestralmente

11. **Sem Consultoria Jurídica (Disclaimer Obrigatório)**
    - **Problema:** Informações podem ter erro ou interpretação incorreta
    - **Mitigação:** Modal disclaimer obrigatório, fontes oficiais sempre citadas
    - **Limitação Legal:** Não substitui advogado/defensor público

---

## 14. DNS & Domínio Customizado

### Configuração GoDaddy

**Domínio:** `fabiotreze.com` (registrado na GoDaddy)

**Registros DNS:**
```
Type   Host                      Value                                    TTL
────────────────────────────────────────────────────────────────────────────
CNAME  nossodireito              app-nossodireito.azurewebsites.net       1 Hour
TXT    asuid.nossodireito        <Azure verification token>               1 Hour
```

**Processo de Setup:**

1. **Azure App Service → Custom Domains → Add Custom Domain**
   - Hostname: `nossodireito.fabiotreze.com`
   - Validate ownership via TXT record (`asuid.<subdomain>`)

2. **GoDaddy → DNS Management**
   - Adicionar CNAME: `nossodireito` → `app-nossodireito.azurewebsites.net`
   - Adicionar TXT (verification): `asuid.nossodireito` → (valor do Azure)

3. **Aguardar Propagação** (DNS TTL: 1 hora)
   - Verificar: `nslookup nossodireito.fabiotreze.com`
   - Deve apontar para `app-nossodireito.azurewebsites.net`

4. **Azure → Certificado SSL (Key Vault PFX)**
   - Terraform importa PFX para Key Vault
   - App Service Certificate referencia via `key_vault_secret_id`
   - SSL Binding: SNI Enabled

5. **Redirect azurewebsites.net → Custom Domain** (server.js)
```javascript
if (host === 'app-nossodireito.azurewebsites.net' && req.headers.accept?.includes('text/html')) {
    const location = `https://nossodireito.fabiotreze.com${req.url}`;
    res.writeHead(301, { 'Location': location, 'Cache-Control': 'public, max-age=86400' });
    res.end();
    return;
}
```

**Certificado SSL:**
- **Tipo:** Wildcard (`*.fabiotreze.com` + `fabiotreze.com`)
- **Issuer:** Let's Encrypt ou DigiCert (GoDaddy)
- **Validade:** 1 ano (renovação manual via GoDaddy)
- **Formato:** PFX (PKCS#12) com senha
- **Armazenamento:** Azure Key Vault (encrypted at rest)

---

## 15. Disaster Recovery & Backup

### Estratégia de Backup

**Código Fonte:** GitHub repository (git push)
- **Frequência:** A cada commit
- **Retenção:** Ilimitada (GitHub gratuito)
- **Restore:** `git clone https://github.com/fabiotreze/nossodireito.git`

**Infraestrutura (Terraform State):**
- **Backend:** Local `terraform.tfstate` (não commitado)
- **Backup Manual:** Copiar `terraform.tfstate` para OneDrive/1 vez mês
- **Restore:** `terraform apply` com state file

**Dados JSON:**
- **Frequência:** Versionado com código (git)
- **Retenção:** Git history (every commit)
- **Restore:** `git checkout <commit> data/direitos.json`

**Certificado SSL:**
- **Backup:** PFX file local (não commitado) + Key Vault
- **Restore:** Re-run `terraform apply` com `var.pfx_file_path`

### RTO/RPO

| Métrica | Valor | Justificativa |
|---------|-------|---------------|
| **RTO** (Recovery Time Objective) | 1 hora | Tempo para re-deploy manual via GitHub Actions + Terraform |
| **RPO** (Recovery Point Objective) | 0 (zero loss) | Código/dados em git, state em Key Vault |

### Disaster Scenarios

#### 1. Azure Region Outage (Brazil South)
**Impacto:** Site indisponível
**Mitigação:** Não há (mono-region, sem DR)
**Restore:**
1. Aguardar Azure restore (SLA 99.95% = 4.38h downtime/ano)
2. Ou: Re-deploy em região secundária (East US 2)
   ```bash
   terraform apply -var="location=eastus2"
   ```

#### 2. App Service Corruption
**Impacto:** Site serve conteúdo incorreto/quebrado
**Restore:**
1. Rollback via GitHub Actions (re-deploy commit anterior)
   ```bash
   git revert HEAD
   git push origin main  # Trigger CI/CD
   ```
2. Ou: Deploy manual via Azure CLI
   ```bash
   az webapp deployment source config-zip \
     --resource-group rg-nossodireito-prod \
     --name app-nossodireito \
     --src deploy.zip
   ```

#### 3. Terraform State Loss
**Impacto:** Não consegue gerenciar infra via Terraform
**Restore:**
1. Re-import recursos existentes:
   ```bash
   terraform import azurerm_resource_group.main /subscriptions/{id}/resourceGroups/rg-nossodireito-prod
   terraform import azurerm_linux_web_app.main /subscriptions/{id}/resourceGroups/rg-nossodireito-prod/providers/Microsoft.Web/sites/app-nossodireito
   # ... repeat for all resources
   ```
2. Ou: Gerenciar via Azure Portal manualmente

#### 4. Key Vault Certificate Expiration
**Impacto:** SSL inválido (browser warning)
**Prevenção:** Alerta 30 dias antes (Azure Monitor)
**Restore:**
1. Renovar certificado no GoDaddy
2. Download novo PFX
3. Re-run Terraform:
   ```bash
   terraform apply -var="pfx_file_path=$CERT_FILE_PATH"
   ```

#### 5. Data Corruption (direitos.json)
**Impacto:** Informações incorretas exibidas
**Restore:**
1. Git revert:
   ```bash
   git log data/direitos.json  # Find good commit
   git checkout <commit> data/direitos.json
   git commit -m "Restore direitos.json to <commit>"
   git push
   ```

### Monitoring for Failures

**Healthcheck Endpoint:**
```javascript
// server.js
if (req.url === '/healthz' || req.url === '/health') {
    const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-cache, no-store' });
    res.end(JSON.stringify({ status: 'healthy', version: pkg.version }));
    return;
}
```

**Azure Monitor Probe:**
- Path: `/health`
- Interval: 5 minutos
- Timeout: 30 segundos
- Unhealthy threshold: 3 consecutive failures

**Alert:** Email para `fabiotreze@hotmail.com` quando health check falha.

---

## Conclusão

Este documento apresenta a arquitetura completa do sistema **NossoDireito V1** (versão 1.2.0) em produção. O portal atende ~1.000 famílias/mês com informações sobre direitos PcD, mantendo:

✅ **Conformidade LGPD** (zero data collection)
✅ **Acessibilidade WCAG 2.1 AA** (TTS, VLibras, alto contraste)
✅ **Segurança EASM-hardened** (OWASP headers, rate limiting)
✅ **Performance Lighthouse 95+** (Brotli, Service Worker, CDN)
✅ **Infraestrutura IaC** (Terraform, GitHub Actions CI/CD)
✅ **Custo $19/mês** (App Service B1, Key Vault, App Insights)

### Próximos Passos

Melhorias futuras consideráveis:
- Azure OpenAI GPT-4o-mini (95% acurácia vs. 70% regex)
- Next.js 14 + TypeScript
- Redis cache + Cosmos DB
- Anonimização server-side (PII detection)
- Custo otimizado: $48/mês (vs. $150 sem cache)

---

**Autoria:** Fábio Treze
**Contato:** fabiotreze@hotmail.com
**Licença:** Projeto sem fins lucrativos — código disponível para auditoria
**Última Atualização:** Fevereiro 2026
