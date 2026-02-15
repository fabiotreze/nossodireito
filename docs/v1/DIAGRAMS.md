# NossoDireito — Diagramas Completos do Sistema V1

**Versão:** 1.2.0  
**Data:** Fevereiro 2026  
**Tipo:** Documentação Visual da Arquitetura  

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Diagrama 1: Arquitetura Geral](#2-diagrama-1-arquitetura-geral)
3. [Diagrama 2: Fluxo de Dados - Interação do Usuário](#3-diagrama-2-fluxo-de-dados---interação-do-usuário)
4. [Diagrama 3: Infraestrutura Terraform (Azure)](#4-diagrama-3-infraestrutura-terraform-azure)
5. [Diagrama 4: Módulos Client-Side (JavaScript)](#5-diagrama-4-módulos-client-side-javascript)
6. [Diagrama 5: Camadas de Segurança](#6-diagrama-5-camadas-de-segurança)
7. [Diagrama 6: CI/CD Pipeline](#7-diagrama-6-cicd-pipeline)
8. [Diagrama 7: Conformidade LGPD](#8-diagrama-7-conformidade-lgpd)
9. [Legenda de Cores](#9-legenda-de-cores)

---

## 1. Visão Geral

Este documento apresenta **7 diagramas Mermaid** que cobrem toda a arquitetura do sistema NossoDireito V1:

- **Infraestrutura** (Azure, Terraform, GoDaddy)
- **Código** (server.js, app.js, módulos client-side)
- **Fluxos de dados** (usuário → servidor → browser)
- **Segurança** (EASM, OWASP, CSP, rate limiting)
- **CI/CD** (GitHub Actions, deploy, quality gate)
- **Conformidade** (LGPD Art. 4º, zero-data architecture)

**Ferramentas de Visualização:**
- GitHub Markdown (renderiza Mermaid nativamente)
- VS Code + Markdown Preview Mermaid Extension
- [Mermaid Live Editor](https://mermaid.live) para edição online

---

## 2. Diagrama 1: Arquitetura Geral

**Propósito:** Visão de alto nível mostrando todos os componentes do sistema, desde o usuário final até Azure Cloud, passando por DNS, CDN, App Service, Key Vault, monitoring e client-side storage.

```mermaid
graph TB
    subgraph "Usuário Final"
        Browser[Browser/PWA<br/>Chrome, Safari, Edge]
        Mobile[Mobile Browser<br/>iOS, Android]
    end
    
    subgraph "DNS & CDN Layer"
        GoDaddy[GoDaddy DNS<br/>nossodireito.fabiotreze.com]
        CDN[Azure Front Door<br/>Implicit CDN<br/>HTTP/2 + Brotli]
    end
    
    subgraph "Azure Cloud - Brazil South"
        subgraph "App Service Plan - B1 Linux"
            AppService[Azure App Service<br/>app-nossodireito<br/>Node.js 22 LTS<br/>Always On]
            NodeJS[server.js<br/>Static File Server<br/>420 lines<br/>Security Headers]
        end
        
        subgraph "Security & Secrets"
            KeyVault[Azure Key Vault<br/>Standard<br/>SSL Certificate PFX]
            ManagedID[Managed Identity<br/>System-Assigned]
        end
        
        subgraph "Monitoring & Logs"
            AppInsights[Application Insights<br/>Node.JS Type<br/>Telemetry]
            LogAnalytics[Log Analytics<br/>30 days retention<br/>KQL queries]
            Alerts[Monitor Alerts<br/>5xx, Health, Latency]
        end
    end
    
    subgraph "Static Assets Served"
        HTML[index.html<br/>568 lines<br/>SPA Shell]
        CSS[styles.css<br/>2,862 lines<br/>Dark Mode]
        JS[app.js<br/>2,682 lines<br/>Vanilla JS]
        SW[sw.js<br/>158 lines<br/>Cache-First]
        Data1[direitos.json<br/>2,293 lines<br/>9 Categories]
        Data2[matching_engine.json<br/>2,716 lines<br/>CID + Keywords]
    end
    
    subgraph "Client-Side Storage"
        IDB[IndexedDB<br/>AES-GCM-256<br/>PDFs encrypted<br/>TTL 30min]
        LS[localStorage<br/>Preferences<br/>Checklist State]
        Cache[Service Worker Cache<br/>Offline-First]
    end
    
    subgraph "External Dependencies"
        PDFjs[PDF.js CDN<br/>CloudFlare<br/>3.11.174]
        VLibras[VLibras Gov.br<br/>Unity WebGL<br/>Libras Widget]
    end
    
    Browser --> GoDaddy
    Mobile --> GoDaddy
    GoDaddy -->|CNAME| CDN
    CDN --> AppService
    
    AppService --> NodeJS
    NodeJS --> HTML
    NodeJS --> CSS
    NodeJS --> JS
    NodeJS --> SW
    NodeJS --> Data1
    NodeJS --> Data2
    
    NodeJS --> AppInsights
    AppInsights --> LogAnalytics
    LogAnalytics --> Alerts
    
    AppService --> ManagedID
    ManagedID -->|Read Certificate| KeyVault
    
    Browser --> IDB
    Browser --> LS
    Browser --> Cache
    Browser --> PDFjs
    Browser --> VLibras
    
    style AppService fill:#1e40af,color:#fff
    style NodeJS fill:#059669,color:#fff
    style KeyVault fill:#dc2626,color:#fff
    style AppInsights fill:#f59e0b,color:#000
    style IDB fill:#8b5cf6,color:#fff
    style VLibras fill:#ec4899,color:#fff
```

**Componentes Principais:**
- **GoDaddy DNS**: CNAME `nossodireito.fabiotreze.com` → `app-nossodireito.azurewebsites.net`
- **Azure Front Door**: CDN implícito (HTTP/2, Brotli compression)
- **App Service B1**: Hospeda Node.js 22 LTS rodando `server.js`
- **Key Vault**: Armazena certificado SSL PFX (wildcard `*.fabiotreze.com`)
- **Application Insights**: Telemetria (page views, latência, erros)
- **IndexedDB**: Armazenamento local de PDFs com AES-GCM-256 (TTL 30 min)
- **VLibras**: Widget gov.br para tradução Libras (Unity WebGL)

---

## 3. Diagrama 2: Fluxo de Dados - Interação do Usuário

**Propósito:** Sequence diagram mostrando 5 fluxos principais de interação entre usuário, browser, servidor e serviços externos.

```mermaid
sequenceDiagram
    actor User as Usuário
    participant Browser as Browser
    participant SW as Service Worker
    participant Server as server.js<br/>(Azure App Service)
    participant KV as Key Vault
    participant AI as App Insights
    participant IDB as IndexedDB
    participant PDFjs as PDF.js
    participant VL as VLibras Widget

    Note over User,VL: Fluxo 1: Primeiro Acesso ao Site
    
    User->>Browser: Acessa nossodireito.fabiotreze.com
    Browser->>Server: GET / (HTTPS)
    Server->>KV: Busca certificado SSL
    KV-->>Server: Certificado PFX
    Server->>AI: Log request (IP anonimizado)
    Server-->>Browser: index.html + Security Headers
    
    Browser->>Server: GET /css/styles.css
    Server-->>Browser: styles.css (Brotli compressed)
    
    Browser->>Server: GET /js/app.js
    Server-->>Browser: app.js
    
    Browser->>Server: GET /js/sw-register.js
    Server-->>Browser: sw-register.js
    
    Browser->>SW: Registra Service Worker
    SW->>Browser: Instalação concluída
    SW->>SW: Pre-cache assets estáticos
    
    Browser->>Server: GET /data/direitos.json
    Server-->>Browser: direitos.json (cached por SW)
    
    Browser->>Browser: Exibe disclaimer modal
    User->>Browser: Clica "Entendi"
    Browser->>Browser: localStorage.disclaimerAccepted = true
    
    Note over User,VL: Fluxo 2: Upload e Análise de Laudo PDF
    
    User->>Browser: Upload laudo.pdf
    Browser->>IDB: Gera chave AES-GCM-256
    Browser->>IDB: Encripta PDF
    IDB-->>Browser: ID do arquivo
    
    Browser->>PDFjs: Carrega PDF.js worker
    PDFjs-->>Browser: Worker pronto
    
    Browser->>PDFjs: Extrai texto do PDF
    PDFjs->>PDFjs: Itera páginas 1-N
    PDFjs-->>Browser: Texto completo
    
    Browser->>Browser: Busca CID codes (regex)
    Browser->>Browser: Busca keywords (matching_engine.json)
    Browser->>Browser: Calcula scores por categoria
    Browser-->>User: Exibe 3 direitos identificados
    
    Note over User,VL: Fluxo 3: Acessibilidade (TTS + VLibras)
    
    User->>Browser: Clica botão "🔊 Ouvir"
    Browser->>Browser: Web Speech API synthesize
    Browser-->>User: Voz pt-BR lendo conteúdo
    
    User->>Browser: Clica botão "🤟 Libras"
    Browser->>VL: Carrega vlibras.gov.br/app/vlibras-plugin.js
    VL->>VL: Inicializa Unity WebGL
    VL-->>Browser: Widget avatar 3D pronto
    User->>VL: Clica palavra no texto
    VL-->>User: Avatar traduz em Libras
    
    Note over User,VL: Fluxo 4: Offline (Service Worker Cache)
    
    User->>Browser: Fecha conexão Wi-Fi
    Browser->>SW: GET /data/direitos.json
    SW->>SW: Cache match encontrado
    SW-->>Browser: direitos.json (cached)
    Browser-->>User: Site funciona offline
    
    Note over User,VL: Fluxo 5: Limpeza Automática (TTL)
    
    loop A cada 60 segundos
        Browser->>IDB: Verifica PDFs expirados (>30min)
        IDB->>IDB: Deleta arquivos antigos
    end
```

**Fluxos Detalhados:**

1. **Primeiro Acesso**: Browser faz 6 requests (HTML, CSS, JS, SW, JSON), Service Worker pre-cache todos assets
2. **Análise PDF**: Upload → Encrypt AES-GCM-256 → IndexedDB → PDF.js extrai texto → Regex matching CID + keywords → Score ranking
3. **Acessibilidade**: TTS usa Web Speech API pt-BR, VLibras carrega Unity WebGL widget gov.br
4. **Offline-First**: Service Worker serve assets cached quando sem internet
5. **TTL Auto-cleanup**: Loop limpa PDFs >30 min a cada 60s

---

## 4. Diagrama 3: Infraestrutura Terraform (Azure)

**Propósito:** Todos os recursos Azure provisionados via Terraform IaC (`main.tf` 370 linhas).

```mermaid
graph LR
    subgraph "Terraform Resources"
        RG[azurerm_resource_group<br/>rg-nossodireito-prod<br/>Location: brazilsouth]
        
        ASP[azurerm_service_plan<br/>plan-nossodireito-prod<br/>SKU: B1 Linux<br/>1 vCore, 1.75GB RAM]
        
        App[azurerm_linux_web_app<br/>app-nossodireito<br/>Node.js 22 LTS<br/>Always On: true<br/>HTTPS Only: true]
        
        KV[azurerm_key_vault<br/>kv-nossodireito-prod<br/>SKU: Standard<br/>Soft Delete: 7d]
        
        Cert[azurerm_key_vault_certificate<br/>fabiotreze-wildcard<br/>PFX import from file<br/>*.fabiotreze.com]
        
        AppCert[azurerm_app_service_certificate<br/>cert-app-nossodireito<br/>Key Vault Secret ID]
        
        Domain[azurerm_app_service_custom_hostname_binding<br/>nossodireito.fabiotreze.com]
        
        SSL[azurerm_app_service_certificate_binding<br/>SNI Enabled<br/>SSL State: SniEnabled]
        
        LAW[azurerm_log_analytics_workspace<br/>log-nossodireito-prod<br/>SKU: PerGB2018<br/>Retention: 30 days]
        
        AI[azurerm_application_insights<br/>appi-nossodireito-prod<br/>Type: Node.JS<br/>Workspace: LAW]
        
        AG[azurerm_monitor_action_group<br/>ag-nossodireito-email<br/>Email: fabiotreze@hotmail.com]
        
        Alert1[azurerm_monitor_metric_alert<br/>alert-5xx<br/>Http5xx > 0<br/>Severity: 1]
        
        Alert2[azurerm_monitor_metric_alert<br/>alert-health<br/>HealthCheckStatus < 100<br/>Severity: 0]
        
        Alert3[azurerm_monitor_metric_alert<br/>alert-latency<br/>ResponseTime > 5s<br/>Severity: 2]
        
        Alert4[azurerm_monitor_metric_alert<br/>alert-4xx-spike<br/>Http4xx > 50<br/>Severity: 3]
        
        AP1[azurerm_key_vault_access_policy<br/>deployer<br/>Terraform Service Principal<br/>Full Admin]
        
        AP2[azurerm_key_vault_access_policy<br/>app_service<br/>Managed Identity<br/>Read Certificate]
        
        AP3[azurerm_key_vault_access_policy<br/>web_rp<br/>Microsoft.Web RP<br/>Read for SSL Binding]
    end
    
    RG --> ASP
    ASP --> App
    RG --> KV
    RG --> LAW
    LAW --> AI
    RG --> AG
    
    KV --> Cert
    Cert --> AppCert
    
    App --> Domain
    Domain --> SSL
    AppCert --> SSL
    
    App --> AI
    
    KV --> AP1
    KV --> AP2
    KV --> AP3
    
    App -.->|Managed Identity| AP2
    
    AG --> Alert1
    AG --> Alert2
    AG --> Alert3
    AG --> Alert4
    
    App --> Alert1
    App --> Alert2
    App --> Alert3
    App --> Alert4
    
    style RG fill:#1e40af,color:#fff
    style App fill:#059669,color:#fff
    style KV fill:#dc2626,color:#fff
    style AI fill:#f59e0b,color:#000
    style Alert2 fill:#ef4444,color:#fff
    style SSL fill:#8b5cf6,color:#fff
```

**Recursos Terraform (17 total):**

| Recurso | Tipo | Propósito |
|---------|------|-----------|
| `rg-nossodireito-prod` | Resource Group | Container de todos recursos |
| `plan-nossodireito-prod` | Service Plan | B1 Linux (1 vCore, 1.75GB) |
| `app-nossodireito` | Web App | Hospeda Node.js 22 LTS |
| `kv-nossodireito-prod` | Key Vault | Armazena certificado PFX |
| `fabiotreze-wildcard` | Certificate | PFX importado (*.fabiotreze.com) |
| `cert-app-nossodireito` | App Service Cert | Referencia KV secret |
| `nossodireito.fabiotreze.com` | Custom Hostname | CNAME binding |
| SSL Binding | Certificate Binding | SNI Enabled SSL |
| `log-nossodireito-prod` | Log Analytics | 30 dias retenção |
| `appi-nossodireito-prod` | App Insights | Telemetria Node.JS |
| `ag-nossodireito-email` | Action Group | Email alerts |
| 4x Metric Alerts | Monitor Alerts | 5xx, health, latency, 4xx |
| 3x Access Policies | Key Vault Policies | Deployer, App, Web RP |

**Comandos Terraform:**
```bash
terraform init          # Download providers
terraform validate      # Syntax check
terraform plan          # Preview changes
terraform apply         # Provision infra
terraform output        # Show outputs (URL, keys)
```

---

## 5. Diagrama 4: Módulos Client-Side (JavaScript)

**Propósito:** Estrutura interna do `app.js` (2.682 linhas) dividido em 8 módulos funcionais.

```mermaid
graph TD
    subgraph "Client-Side Components - app.js 2,682 lines"
        App[app.js Entry Point]
        
        subgraph "TTS Engine Module"
            TTS[TTSEngine Class]
            TTS_Init[selectBrazilianVoice]
            TTS_Speak[speak method]
            TTS_Chunk[chunkText 1000 chars]
            TTS_Stop[stop method]
        end
        
        subgraph "VLibras Integration"
            VL[initVLibras function]
            VL_Load[Load vlibras-plugin.js]
            VL_Widget[VLibras.Widget instance]
            VL_Move[Move button to toolbar]
        end
        
        subgraph "PDF Analysis Engine"
            PDF[PDFAnalyzer Class]
            PDF_Load[Load PDF via ArrayBuffer]
            PDF_Extract[Extract text all pages]
            PDF_CID[extractCIDs regex]
            PDF_Keywords[extractKeywords weighted]
            PDF_Score[calculateScores sum]
            PDF_Rank[Sort by score desc]
        end
        
        subgraph "IndexedDB Manager"
            IDB[IndexedDBManager Class]
            IDB_Init[init database]
            IDB_Save[savePDF AES-GCM-256]
            IDB_Get[getPDF decrypt]
            IDB_Delete[deletePDF]
            IDB_Clean[cleanExpired TTL 30min]
        end
        
        subgraph "UI Renderer"
            UI[UI Module]
            UI_Cards[renderCategoryCards]
            UI_Search[searchFilter]
            UI_Modal[modalManager]
            UI_Accordion[accordionToggle]
            UI_Checklist[checklistProgressBar]
        end
        
        subgraph "Accessibility Controller"
            A11y[A11y Toolbar]
            A11y_Font[Font size ± reset]
            A11y_Contrast[High contrast toggle]
            A11y_Keyboard[Keyboard navigation Tab Enter Space]
            A11y_Focus[Focus visible outline 3px]
        end
        
        subgraph "Data Loading"
            Data[Data Loader]
            Data_Direitos[Fetch direitos.json]
            Data_Matching[Fetch matching_engine.json]
            Data_Cache[Service Worker cache]
        end
        
        subgraph "Event Listeners"
            Events[Event Handlers]
            Events_Upload[PDF upload input]
            Events_Buttons[Button clicks toolbar]
            Events_Forms[Checklist checkboxes]
            Events_Nav[Navigation menu toggle]
        end
    end
    
    App --> TTS
    App --> VL
    App --> PDF
    App --> IDB
    App --> UI
    App --> A11y
    App --> Data
    App --> Events
    
    TTS --> TTS_Init
    TTS --> TTS_Speak
    TTS_Speak --> TTS_Chunk
    TTS --> TTS_Stop
    
    VL --> VL_Load
    VL_Load --> VL_Widget
    VL_Widget --> VL_Move
    
    PDF --> PDF_Load
    PDF_Load --> PDF_Extract
    PDF_Extract --> PDF_CID
    PDF_Extract --> PDF_Keywords
    PDF_CID --> PDF_Score
    PDF_Keywords --> PDF_Score
    PDF_Score --> PDF_Rank
    
    IDB --> IDB_Init
    IDB --> IDB_Save
    IDB --> IDB_Get
    IDB --> IDB_Delete
    IDB --> IDB_Clean
    
    UI --> UI_Cards
    UI --> UI_Search
    UI --> UI_Modal
    UI --> UI_Accordion
    UI --> UI_Checklist
    
    A11y --> A11y_Font
    A11y --> A11y_Contrast
    A11y --> A11y_Keyboard
    A11y --> A11y_Focus
    
    Data --> Data_Direitos
    Data --> Data_Matching
    Data --> Data_Cache
    
    Events --> Events_Upload
    Events --> Events_Buttons
    Events --> Events_Forms
    Events --> Events_Nav
    
    Events_Upload --> PDF
    Events_Upload --> IDB
    PDF --> UI_Cards
    
    Events_Buttons --> TTS
    Events_Buttons --> VL
    Events_Buttons --> A11y
    
    Data_Direitos --> UI_Cards
    Data_Matching --> PDF
    
    style App fill:#1e40af,color:#fff
    style TTS fill:#059669,color:#fff
    style PDF fill:#f59e0b,color:#000
    style IDB fill:#8b5cf6,color:#fff
    style A11y fill:#ec4899,color:#fff
```

**Módulos JavaScript:**

1. **TTS Engine**: Web Speech API, voz pt-BR, chunking 1000 chars
2. **VLibras**: Unity WebGL widget gov.br, avatar Icaro/Hosana
3. **PDF Analyzer**: PDF.js extraction, CID regex, keyword weighting, score ranking
4. **IndexedDB**: AES-GCM-256 encryption, TTL 30 min, auto-cleanup 60s
5. **UI Renderer**: Dynamic cards, accordion, modal, search filter
6. **A11y Toolbar**: Font ±, high contrast, keyboard nav, focus visible
7. **Data Loader**: Fetch JSON, Service Worker cache strategy
8. **Event Handlers**: Upload, buttons, forms, navigation

---

## 6. Diagrama 5: Camadas de Segurança

**Propósito:** Defense in depth com 5 camadas de segurança (Platform → Application → Input → Client → Monitoring).

```mermaid
graph TB
    subgraph "Security Layers - Defense in Depth"
        
        subgraph "Layer 1: Azure Platform"
            DDoS[DDoS Protection Basic<br/>Included free<br/>Auto-mitigation]
            WAF[Azure Front Door<br/>Implicit WAF capabilities<br/>HTTP/2 + TLS 1.3]
            SSL[SSL/TLS Certificate<br/>Wildcard PFX<br/>SNI Binding<br/>Key Vault encrypted]
        end
        
        subgraph "Layer 2: server.js Application"
            Headers[Security Headers<br/>14 OWASP headers]
            CSP[Content-Security-Policy<br/>Whitelist approach<br/>default-src none]
            HSTS[Strict-Transport-Security<br/>max-age 1 year<br/>includeSubDomains<br/>preload]
            XFrame[X-Frame-Options: DENY<br/>Prevents clickjacking]
            XCTO[X-Content-Type-Options<br/>nosniff]
            PermPolicy[Permissions-Policy<br/>Disable camera, mic, geo]
            COOP[Cross-Origin-Opener-Policy<br/>same-origin]
            CORP[Cross-Origin-Resource-Policy<br/>cross-origin for VLibras]
            COEP[Cross-Origin-Embedder-Policy<br/>unsafe-none for Unity]
        end
        
        subgraph "Layer 3: Input Validation"
            RateLimit[Rate Limiting<br/>120 req/min per IP<br/>In-memory Map]
            PathTraversal[Path Traversal Protection<br/>Reject .. and null bytes<br/>CWE-22]
            ExtWhitelist[Extension Whitelist<br/>Only .html .css .js .json .png<br/>CWE-434]
            HostValidation[Host Header Validation<br/>Exact match whitelist<br/>CWE-644]
            MethodWhitelist[Method Whitelist<br/>GET HEAD only<br/>Reject POST PUT DELETE]
        end
        
        subgraph "Layer 4: Client-Side"
            IndexedDB[IndexedDB Encryption<br/>AES-GCM-256<br/>TTL 30 minutes]
            NoServerUpload[Zero Server Upload<br/>PDFs never transmitted<br/>100% local processing]
            localStorage[localStorage Clearable<br/>User can delete anytime<br/>Preferences only]
        end
        
        subgraph "Layer 5: Monitoring & Detection"
            AppInsights[Application Insights<br/>Real-time telemetry<br/>IP anonymization]
            Alerts_5xx[Alert: HTTP 5xx<br/>Severity 1<br/>Email notification]
            Alerts_Health[Alert: Health Check Fail<br/>Severity 0<br/>Critical]
            Alerts_Latency[Alert: Latency > 5s<br/>Severity 2<br/>Performance]
            Alerts_4xx[Alert: 4xx Spike > 50<br/>Severity 3<br/>Possible attack]
        end
        
        subgraph "Known Vulnerabilities Accepted"
            CSP_Eval[CSP: unsafe-eval<br/>Required for VLibras Unity<br/>Risk: Medium<br/>Mitigated by origin whitelist]
            CSP_Inline[CSP: unsafe-inline style<br/>VLibras dynamic CSS<br/>Risk: Low<br/>No alternative]
            RateLimit_Mem[Rate Limit: In-memory<br/>DDoS distributed bypass<br/>Risk: Medium<br/>Trade-off cost vs security]
        end
    end
    
    DDoS --> WAF
    WAF --> SSL
    SSL --> Headers
    
    Headers --> CSP
    Headers --> HSTS
    Headers --> XFrame
    Headers --> XCTO
    Headers --> PermPolicy
    Headers --> COOP
    Headers --> CORP
    Headers --> COEP
    
    Headers --> RateLimit
    Headers --> PathTraversal
    Headers --> ExtWhitelist
    Headers --> HostValidation
    Headers --> MethodWhitelist
    
    RateLimit --> IndexedDB
    PathTraversal --> NoServerUpload
    ExtWhitelist --> localStorage
    
    AppInsights --> Alerts_5xx
    AppInsights --> Alerts_Health
    AppInsights --> Alerts_Latency
    AppInsights --> Alerts_4xx
    
    CSP -.->|Exception| CSP_Eval
    CSP -.->|Exception| CSP_Inline
    RateLimit -.->|Limitation| RateLimit_Mem
    
    style DDoS fill:#1e40af,color:#fff
    style CSP fill:#dc2626,color:#fff
    style IndexedDB fill:#8b5cf6,color:#fff
    style Alerts_Health fill:#ef4444,color:#fff
    style CSP_Eval fill:#fbbf24,color:#000
    style CSP_Inline fill:#fbbf24,color:#000
    style RateLimit_Mem fill:#fbbf24,color:#000
```

**Mitigação de Vulnerabilidades (CWE):**

| CWE | Vulnerabilidade | Mitigação |
|-----|-----------------|-----------|
| CWE-22 | Path Traversal | Reject `..`, normalize paths, `startsWith(ROOT)` |
| CWE-158 | Null Byte Injection | Reject `\0` in URLs |
| CWE-116 | Control Characters | Reject `[\x00-\x1f\x7f]` |
| CWE-400 | Resource Exhaustion | Max URL 2048, timeout 30s |
| CWE-434 | Unrestricted Upload | Extension whitelist only |
| CWE-644 | Host Header Poisoning | Exact match whitelist |
| CWE-770 | Allocation w/o Limits | Rate limit 120 req/min |
| CWE-200 | Information Exposure | Suppress `X-Powered-By`, block `/terraform` |
| CWE-693 | Protection Failure | 14 security headers (CSP, HSTS, etc.) |

**Vulnerabilidades Aceitas:**
- `unsafe-eval` em CSP: Necessário para VLibras Unity WebAssembly (trade-off funcionalidade vs. segurança)
- `unsafe-inline` em `style-src`: VLibras injeta CSS dinamicamente (sem alternativa)
- Rate limiting in-memory: DDoS distribuído não mitigado (trade-off custo Redis vs. simplicidade)

---

## 7. Diagrama 6: CI/CD Pipeline

**Propósito:** Workflow GitHub Actions para quality gate (PR validation) e deployment (push to main).

```mermaid
graph LR
    subgraph "GitHub Repository"
        Code[Source Code<br/>HTML, CSS, JS, JSON]
        TF[Terraform IaC<br/>main.tf, variables.tf]
        Scripts[Python Scripts<br/>validate_sources.py<br/>bump_version.py]
        Workflows[GitHub Actions<br/>deploy.yml<br/>quality-gate.yml]
    end
    
    subgraph "CI Pipeline - Quality Gate"
        PR[Pull Request Trigger]
        Validate[Run validate_sources.py<br/>Check .gov.br URLs]
        Lint[JSON syntax check<br/>jq empty *.json]
        Audit[npm audit<br/>Security vulnerabilities]
        Tests[Unit tests<br/>Not implemented yet]
    end
    
    subgraph "CD Pipeline - Deployment"
        Push[Push to main branch]
        Checkout[Checkout code<br/>actions/checkout@v4]
        NodeSetup[Setup Node.js 22<br/>actions/setup-node@v4]
        InstallDeps[npm ci<br/>Install applicationinsights]
        AzLogin[Azure Login<br/>Service Principal JSON]
        Deploy[Deploy App Service<br/>azure/webapps-deploy@v2]
        HealthCheck[Verify /health<br/>curl -f https://nossodireito...]
    end
    
    subgraph "Terraform Workflow Manual"
        TF_Init[terraform init<br/>Download azurerm provider]
        TF_Validate[terraform validate<br/>Syntax check]
        TF_Plan[terraform plan<br/>Dry-run preview changes]
        TF_Apply[terraform apply<br/>Provision Azure resources]
        TF_Output[terraform output<br/>App URL, Insights key]
    end
    
    subgraph "Azure App Service"
        AppSvc[app-nossodireito<br/>Running on B1 Linux]
        Kudu[Kudu SCM<br/>Deployment logs<br/>SSH console]
    end
    
    Code --> PR
    Code --> Push
    
    PR --> Validate
    Validate --> Lint
    Lint --> Audit
    Audit --> Tests
    
    Tests -.->|Pass| Merge[Merge to main]
    Merge --> Push
    
    Push --> Checkout
    Checkout --> NodeSetup
    NodeSetup --> InstallDeps
    InstallDeps --> AzLogin
    AzLogin --> Deploy
    Deploy --> AppSvc
    AppSvc --> HealthCheck
    
    HealthCheck -.->|200 OK| Success[Deployment Success]
    HealthCheck -.->|Non-200| Rollback[Manual Rollback]
    
    TF --> TF_Init
    TF_Init --> TF_Validate
    TF_Validate --> TF_Plan
    TF_Plan --> TF_Apply
    TF_Apply --> AppSvc
    TF_Apply --> TF_Output
    
    AppSvc --> Kudu
    
    style Push fill:#1e40af,color:#fff
    style Deploy fill:#059669,color:#fff
    style TF_Apply fill:#f59e0b,color:#000
    style Success fill:#16a34a,color:#fff
    style Rollback fill:#dc2626,color:#fff
```

**Workflows GitHub Actions:**

1. **quality-gate.yml** (PR trigger):
   - `validate_sources.py`: Valida URLs .gov.br em `direitos.json`
   - `jq empty`: Verifica sintaxe JSON
   - `npm audit`: Scan vulnerabilidades de segurança
   - Unit tests: Não implementado (TODO)

2. **deploy.yml** (Push to main):
   - Checkout código
   - Setup Node.js 22
   - `npm ci` instala applicationinsights
   - Azure login com Service Principal
   - Deploy para App Service via `azure/webapps-deploy@v2`
   - Health check `/health` (200 OK = success)

3. **Terraform (Manual)**:
   - `terraform init`: Baixa provider azurerm
   - `terraform validate`: Syntax check
   - `terraform plan`: Preview mudanças
   - `terraform apply`: Provisiona infra
   - `terraform output`: Exibe URLs/keys

---

## 8. Diagrama 7: Conformidade LGPD

**Propósito:** Arquitetura zero-data collection que garante conformidade LGPD Art. 4º, I.

```mermaid
graph TB
    subgraph "LGPD Compliance Architecture"
        
        subgraph "Data Processing Principle"
            Art4[LGPD Art. 4º, I<br/>"Não se aplica a dados<br/>que não são objeto<br/>de tratamento"]
            ZeroCollection[Zero Data Collection<br/>Nenhum dado pessoal<br/>chega ao servidor]
        end
        
        subgraph "Server-Side - Azure App Service"
            Server[server.js<br/>Static File Server]
            NoPost[Reject POST/PUT/DELETE<br/>Somente GET/HEAD]
            NoCookies[Zero Cookies<br/>Sem tracking]
            NoForm[form-action: none<br/>CSP header]
            NoPersist[Zero Persistência<br/>Não grava uploads]
        end
        
        subgraph "Client-Side - Browser Storage"
            IndexedDB[IndexedDB<br/>nossoDireitoDB]
            PDFs[PDFs: AES-GCM-256<br/>TTL 30 minutos<br/>Auto-delete]
            LocalStorage[localStorage<br/>Preferences Only]
            Prefs[disclaimerAccepted: boolean<br/>fontSize: number<br/>highContrast: boolean<br/>checklist progress]
            ClearBtn[Botão "Apagar Dados"<br/>User-controlled deletion]
        end
        
        subgraph "Telemetry - Application Insights"
            AI[Azure App Insights<br/>Microsoft Analytics]
            
            Collected[Dados Coletados:<br/>✅ Page views URL path<br/>✅ IP anonimizado últimos 2 octets<br/>✅ Geolocalização País/Estado<br/>✅ User-Agent Browser/OS<br/>✅ Response time ms<br/>✅ HTTP status codes]
            
            NotCollected[Dados NÃO Coletados:<br/>❌ Conteúdo de PDFs<br/>❌ Texto de buscas<br/>❌ Estado de checkboxes<br/>❌ Nomes, CPFs, RGs<br/>❌ Cookies/fingerprinting<br/>❌ Query params sensíveis]
            
            LegalBasis[Base Legal:<br/>Legítimo Interesse Art. 10<br/>Segurança cibernética<br/>Prevenção de fraude]
        end
        
        subgraph "Transparency - Disclaimer Modal"
            Modal[Modal Obrigatório<br/>Primeiro Acesso]
            DisclaimerText["🔒 Privacidade LGPD:<br/>- Zero coleta de dados pessoais<br/>- Análise 100% local browser<br/>- localStorage clearable<br/>- VLibras sem envio dados"]
            Accept[Botão "Entendi"<br/>localStorage.disclaimerAccepted]
        end
        
        subgraph "Data Flow Validation"
            Upload[Usuário faz upload PDF]
            BrowserOnly[PDF.js extrai texto<br/>SOMENTE no browser]
            NoTransmit[Zero transmissão rede<br/>Nenhum byte enviado servidor]
            EncryptLocal[Encripta AES-GCM-256<br/>Salva IndexedDB local]
            TTL[TTL 30 min<br/>Auto-delete sweep 60s]
        end
    end
    
    Art4 --> ZeroCollection
    ZeroCollection --> Server
    
    Server --> NoPost
    Server --> NoCookies
    Server --> NoForm
    Server --> NoPersist
    
    Server --> IndexedDB
    IndexedDB --> PDFs
    IndexedDB --> LocalStorage
    LocalStorage --> Prefs
    Prefs --> ClearBtn
    
    Server --> AI
    AI --> Collected
    AI --> NotCollected
    AI --> LegalBasis
    
    Modal --> DisclaimerText
    DisclaimerText --> Accept
    
    Upload --> BrowserOnly
    BrowserOnly --> NoTransmit
    NoTransmit --> EncryptLocal
    EncryptLocal --> TTL
    
    style Art4 fill:#1e40af,color:#fff
    style ZeroCollection fill:#059669,color:#fff
    style NoTransmit fill:#16a34a,color:#fff
    style NotCollected fill:#dc2626,color:#fff
    style LegalBasis fill:#f59e0b,color:#000
    style PDFs fill:#8b5cf6,color:#fff
```

**LGPD Art. 4º, I - Não Aplicabilidade:**

> "Esta Lei não se aplica ao tratamento de dados pessoais: I - realizado por pessoa natural para fins exclusivamente particulares e não econômicos"

**Arquitetura Zero-Data:**
- ✅ Server aceita somente GET/HEAD (POST/PUT/DELETE rejeitados)
- ✅ Zero cookies (sem tracking)
- ✅ Zero persistência de uploads (PDFs não chegam ao servidor)
- ✅ IndexedDB client-side com AES-GCM-256 + TTL 30 min
- ✅ localStorage clearable pelo usuário (botão "Apagar Dados")
- ✅ Application Insights: IPs anonimizados (últimos 2 octets mascarados)

**Exceção - Telemetria (Base Legal: Legítimo Interesse Art. 10):**
- Page views, geolocalizados (país/estado), User-Agent
- Justificativa: Segurança cibernética, prevenção de fraude, otimização de performance

**Transparência:**
- Modal disclaimer obrigatório no primeiro acesso
- Explica zero-data collection, análise local, localStorage clearable
- Usuário deve clicar "Entendi" para prosseguir

---

## 9. Legenda de Cores

Os diagramas usam cores consistentes para facilitar identificação visual:

| Cor | Hexcode | Uso |
|-----|---------|-----|
| 🔵 **Azul Escuro** | `#1e40af` | **Componentes principais** (App Service, Resource Group, LGPD Art. 4º) |
| 🟢 **Verde** | `#059669` | **Processamento/Lógica** (server.js, TTS Engine, Deploy success) |
| 🔴 **Vermelho** | `#dc2626` | **Segurança crítica** (Key Vault, CSP, dados não coletados) |
| 🟠 **Laranja** | `#f59e0b` | **Monitoramento/Observabilidade** (App Insights, PDF Analyzer, alertas médios) |
| 🟣 **Roxo** | `#8b5cf6` | **Armazenamento/Dados** (IndexedDB, PDFs encriptados, SSL binding) |
| 🔴 **Vermelho Claro** | `#ef4444` | **Alertas críticos** (Health check failures, severity 0) |
| 🟡 **Amarelo** | `#fbbf24` | **Vulnerabilidades aceitas** (CSP exceptions, rate limit limitations) |
| 🟢 **Verde Claro** | `#16a34a` | **Sucesso** (Deployment success, zero-transmit validation) |
| 🩷 **Pink** | `#ec4899` | **Acessibilidade** (VLibras, A11y toolbar) |

---

## Uso dos Diagramas

### GitHub
Os diagramas Mermaid renderizam nativamente no GitHub Markdown. Visualize este arquivo no navegador no repositório.

### VS Code
Instale a extensão [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) para preview local.

### Mermaid Live Editor
Copie o código Mermaid para [mermaid.live](https://mermaid.live) para edição online e exportação PNG/SVG.

### Documentação de Patente
Estes diagramas atendem requisitos de documentação técnica para registro de software, incluindo:
- Arquitetura completa do sistema
- Fluxos de dados e processos
- Infraestrutura como código (IaC)
- Conformidade regulatória (LGPD)
- Segurança defense-in-depth
- CI/CD DevOps pipeline

---

**Autoria:** Fábio Treze  
**Contato:** fabiotreze@hotmail.com  
**Licença:** Projeto sem fins lucrativos — diagramas disponíveis para auditoria  
**Última Atualização:** Fevereiro 2026
