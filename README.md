<p align="center">
  <img src="images/nossodireito-400.png" alt="NossoDireito" width="120">
</p>

# ⚖️ NossoDireito

[![Compliance](https://img.shields.io/badge/Compliance-LGPD%20Current%20State-brightgreen?style=flat-square)](docs/SECURITY-LGPD.md)
[![Azure WAF](https://img.shields.io/badge/Azure%20WAF-Aligned-success?style=flat-square&logo=microsoftazure)](docs/ARCHITECTURE.md)
[![Security](https://img.shields.io/badge/Security-HTTPS%20%7C%20CSP%20%7C%20Zero%20Tracking-green?style=flat-square&logo=letsencrypt)](SECURITY.md)
[![Accessibility](https://img.shields.io/badge/Accessibility-ARIA%20%7C%20VLibras%20%7C%20WCAG-blue?style=flat-square&logo=accessible-icon)](docs/OPERATIONS.md)
[![LGPD](https://img.shields.io/badge/LGPD-Zero%20Data%20Collection-blue?style=flat-square)](docs/SECURITY-LGPD.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/fabiotreze/nossodireito?style=flat-square&label=version)](CHANGELOG.md)
[![Quality Gate](https://github.com/fabiotreze/nossodireito/actions/workflows/quality-gate.yml/badge.svg)](https://github.com/fabiotreze/nossodireito/actions/workflows/quality-gate.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/fabiotreze/nossodireito/quality-gate.yml?label=tests&style=flat-square&logo=pytest)](docs/OPERATIONS.md)
[![CodeQL](https://github.com/fabiotreze/nossodireito/actions/workflows/codeql.yml/badge.svg)](https://github.com/fabiotreze/nossodireito/actions/workflows/codeql.yml)
[![gitleaks](https://github.com/fabiotreze/nossodireito/actions/workflows/gitleaks.yml/badge.svg)](https://github.com/fabiotreze/nossodireito/actions/workflows/gitleaks.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/fabiotreze/nossodireito/badge)](https://securityscorecards.dev/viewer/?uri=github.com/fabiotreze/nossodireito)
[![npm audit](https://img.shields.io/badge/npm%20audit-0%20vulnerabilities-brightgreen?style=flat-square&logo=npm)](package.json)

**Recebeu um laudo? Vem que a gente te ajuda.**

Guia gratuito, sem fins lucrativos, com direitos, benefícios e passo a passo para famílias de pessoas com deficiência (PcD) no Brasil.

🌐 **[nossodireito.fabiotreze.com](https://nossodireito.fabiotreze.com)**

O site continua público para o usuário final, mas o App Service aceita tráfego direto apenas da Cloudflare; o restante da comunicação do app com Azure segue por Private Endpoint e VNet.

O Key Vault agora roda em modo privado por padrão; o apply do Terraform precisa acontecer a partir de um contexto com acesso à VNet para operações de data-plane (ex.: importar PFX e leitura/escrita de segredos).

Por padrão, o segredo `redis-primary-key` não é mais gerenciado pelo Terraform (`manage_redis_secret_with_terraform=false`) para evitar erro 403 em runners fora da VNet quando o Key Vault está fechado.

---

## 📖 Descrição

**NossoDireito** é um guia digital gratuito que centraliza informações sobre direitos, benefícios e procedimentos para pessoas com deficiência (PcD) no Brasil. Desenvolvido com base exclusivamente em **fontes oficiais do governo brasileiro**, o projeto utiliza tecnologia moderna para tornar informações complexas acessíveis a todos.

Quando uma família recebe um laudo médico de deficiência — seja TEA (Transtorno do Espectro Autista), síndrome de Down, deficiência física, visual, auditiva ou intelectual — surge a pergunta: **"E agora? Quais são nossos direitos?"**

Este projeto responde essa pergunta de forma clara, objetiva e validada.

### 🌐 About (English)

**NossoDireito — Rights Portal for People with Disabilities.** Regional project — interface and content in Portuguese (pt-BR) for Brazilian citizens. Web portal with **30 rights categories**, 68 official sources, keyword-based document analysis (609 mapped terms), accessibility tools (VLibras sign language, TTS, high contrast, font scaling), PWA offline support, and encrypted storage via Web Crypto API. **Zero data collection (LGPD compliant).** Master Compliance score 1077.7/1082.7 (99.54%) across 21 validation categories. Infrastructure as Code with Terraform on Azure App Service (region `brazilsouth`), CI/CD via GitHub Actions with automated Quality Gate.

---

## 🚀 Quick Start

```bash
git clone https://github.com/fabiotreze/nossodireito.git
cd nossodireito
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt -r requirements-dev.txt
node server.js                                    # → http://localhost:8080
```

Para rodar testes: veja [`docs/OPERATIONS.md`](docs/OPERATIONS.md)

## 📘 Documentação consolidada (v1.19.0)

- [`docs/README.md`](docs/README.md) — índice da documentação
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — arquitetura e diagrama E2E
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md) — operação e runbook
- [`docs/SECURITY-LGPD.md`](docs/SECURITY-LGPD.md) — baseline de segurança e LGPD
- [`docs/REPLICATION.md`](docs/REPLICATION.md) — replicação para novo tenant/subscription
- [`docs/COST-ESTIMATE.md`](docs/COST-ESTIMATE.md) — itens e baseline para Azure Pricing Calculator

---

## 🎉 NOVIDADES v1.19.0 (18/05/2026) — Replicação, hardening e docs enxutas

**🏆 Status atual:** pipeline de testes 100% verde (678 passed) e baseline de segurança ativa.

### ✅ O que mudou:

1. **Revogação de consentimento IA permanente (LGPD Art. 8º §5)** na interface.
2. **Replicação automatizada** com script de bootstrap para novo tenant/subscription.
3. **Workflow dedicado de replicação** (`.github/workflows/replication.yml`).
4. **Baseline de segurança automatizada** (`.github/workflows/security-baseline.yml`).
5. **Documentação consolidada** em arquitetura/operação/segurança-replicação.

### 📚 Documentação:

- [`docs/README.md`](docs/README.md) — índice da documentação
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — arquitetura atual
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md) — runbook e operação
- [`docs/SECURITY-LGPD.md`](docs/SECURITY-LGPD.md) — segurança e LGPD
- [`docs/REPLICATION.md`](docs/REPLICATION.md) — replicação em novo ambiente
- [`docs/COST-ESTIMATE.md`](docs/COST-ESTIMATE.md) — custos estimados e cenários

---

## ✨ Funcionalidades

### 📋 **30 Categorias de Direitos**

- **BPC/LOAS** — Benefício de Prestação Continuada (1 salário mínimo/mês)
- **CIPTEA** — Carteira de Identificação da Pessoa com TEA
- **Educação Inclusiva** — Matrícula obrigatória, acompanhante especializado
- **Plano de Saúde** — Cobertura obrigatória de terapias (ABA, fono, TO)
- **SUS/Terapias** — Acesso gratuito a reabilitação e medicamentos
- **Transporte** — Passe Livre interestadual, isenções de IPVA/IOF/IPI/ICMS
- **Trabalho** — Cotas PcD em empresas (2% a 5% das vagas)
- **FGTS** — Saque para tratamento ou equipamentos
- **Moradia** — Prioridade no Minha Casa Minha Vida, adaptações em condomínios
- **+ 21 outras categorias** (Isenções tributárias, tecnologia assistiva, meia-entrada, ProUni/FIES/SISU, esporte paralímpico, turismo acessível, curatela, lazer, etc.)

### 🔍 **Busca Inteligente**

- **Matching Engine** com algoritmo de busca semântica
- Reconhece sinônimos e variações (ex: "autismo" → "TEA", "pessoa com deficiência" → "PcD")
- Sistema de pesos para priorizar resultados mais relevantes
- Busca por keywords em 751+ termos mapeados (cobre 6 segmentos: visão, audição, mobilidade, saúde mental, neurodiversidade e fala)

### ♿ **Acessibilidade Máxima**

- **50+ atributos ARIA** (WCAG 2.1 AA/AAA)
- **VLibras** integrado (tradução em Libras do governo federal)
- **Leitura em voz alta** (Web Speech API nativa)
- **Ajuste de fonte** (aumentar/diminuir)
- **Modo alto contraste**
- **PWA** (instalável, funciona offline)
- **Design responsivo** (mobile-first)

### 🔒 **100% Privado**

- **Zero coleta de dados** (LGPD total)
- **Sem cookies de rastreamento**
- **Sem anúncios**
- **Sem cadastro obrigatório**
- Processamento local (navegador do usuário)

### 📚 **Documentação Oficial**

- 40+ leis federais referenciadas com artigos específicos
- URLs verificadas de fontes oficiais (planalto.gov.br, gov.br, inss.gov.br)
- Última atualização: 25 de fevereiro de 2026
- Revisões periódicas

---

## 🚀 Como Usar

### Para Usuários

1. **Acesse** [nossodireito.fabiotreze.com](https://nossodireito.fabiotreze.com)
2. **Busque** pelo benefício ou digite palavras-chave (ex: "autismo", "isenção de imposto", "escola")
3. **Navegue** pelos resultados e clique no benefício desejado
4. **Leia** requisitos, documentos necessários e passo a passo
5. **Ative acessibilidade** (VLibras, voz, contraste) conforme necessidade

### Para Instalação Offline (PWA)

1. No navegador (Chrome/Edge/Safari), acesse o site
2. Clique no ícone de **Instalar** (canto superior direito)
3. App será instalado no dispositivo
4. Funciona **sem internet** após primeira visita

### Para Desenvolvedores

```bash
# Clone o repositório
git clone https://github.com/fabiotreze/nossodireito.git
cd nossodireito

# Instale Python (se necessário para validação)
python3 --version  # Requer 3.10+

# Execute validações
python3 scripts/validate_content.py
python3 scripts/master_compliance.py

# Inicie servidor local
node server.js
# Acesse: http://localhost:8080
```

---

## 🛠️ Tecnologias

### **Frontend**

- **HTML5** — Estrutura semântica (nav, main, section, header, footer)
- **CSS3** — Design responsivo, mobile-first, variáveis CSS
- **JavaScript (Vanilla)** — Zero dependências externas
- **Web Speech API** — Leitura em voz alta nativa
- **Service Worker** — Cache inteligente, funcionalidade offline

### **Dados**

- **JSON** — direitos.json (30 categorias, 265KB) + matching_engine.json (106KB) + dicionario_pcd.json (72KB)
- **Compressão** — Minificação de HTML/CSS/JS

### **Infraestrutura (IaC)**

- **Terraform** — Provisionamento automático Azure
- **Azure App Service** — Hospedagem (Linux, Node.js 22 LTS)
- **Azure Blob Storage** — Armazenamento de assets
- **GitHub Actions** — CI/CD automatizado

### **Validação e Qualidade**

- **Python 3.10+** — Scripts de validação
- **validate_content.py** — 147 verificações de dados e código
- **validate_sources.py** — Teste de HTTP status de 40+ URLs
- **validate_legal_sources.py** — Extração automática de artigos de leis
- **master_compliance.py** — 21 categorias de compliance (score 100%)
- **Pre-commit Hook** — Validação automática antes de cada commit

### **Segurança**

- **HTTPS** obrigatório (Let's Encrypt)
- **CSP** (Content Security Policy) configurado
- **No tracking** (zero cookies de terceiros)
- **LGPD compliant**

### **Acessibilidade**

- **ARIA roles, labels, descriptions** (50+ atributos)
- **VLibras** (gov.br/vlibras)
- **Semântica HTML5**
- **Navegação por teclado**
- **Contraste WCAG AAA**

### **SEO**

- **Meta tags** completas (description, keywords, og:title, og:description)
- **sitemap.xml** atualizado automaticamente
- **robots.txt** configurado
- **Schema.org** markup (FAQPage, BreadcrumbList)
- **Performance** Lighthouse 95+

## ♿ Acessibilidade

- **🔊 Ouvir** — Leitura em voz alta (Web Speech API nativa, sem dependência)
- **🤟 Libras** — Tradução em Libras via VLibras (governo federal)
- **A± Fonte** — Ajuste de tamanho de fonte
- **🔲 Contraste** — Modo alto contraste
- **PWA** — Instalável no celular, funciona offline

## 🔒 Privacidade (LGPD)

- **Nenhum dado pessoal** é coletado, armazenado ou enviado a servidores
- **Zero cookies** de rastreamento
- Todo o processamento ocorre **no navegador do usuário**
- Enquadramento: LGPD Art. 4º, I — tratamento por pessoa natural para fins exclusivamente privados e não econômicos

## 🛠 Tecnologia

| Componente           | Tecnologia                                 |
| -------------------- | ------------------------------------------ |
| Frontend             | HTML5 + CSS3 + Vanilla JavaScript          |
| Acessibilidade       | Web Speech API (TTS) + VLibras (Libras)    |
| PWA                  | Service Worker + manifest.json (offline)   |
| Server               | Node.js 22 LTS (`server.js`)               |
| Base de dados        | JSON estático (`data/direitos.json`)       |
| Criptografia         | AES-GCM-256 via Web Crypto API             |
| Hospedagem           | Azure App Service B1 Linux                 |
| SSL                  | PFX próprio via Azure Key Vault (SNI)      |
| IaC                  | Terraform (azurerm ~>4.0)                  |
| CI/CD                | GitHub Actions (Quality Gate + zip deploy) |
| Monitoramento        | Azure Application Insights                 |
| Analytics de usuário | Nenhum (client-side)                       |
| Cookies              | Nenhum                                     |

## 📁 Estrutura

```
nossodireito/
├── index.html              # Página principal
├── index.min.html          # HTML minificado (produção)
├── server.js               # Servidor Node.js (App Service)
├── package.json            # Dependências (applicationinsights)
├── sw.js                   # Service Worker (PWA offline)
├── manifest.json           # PWA manifest
├── robots.txt              # Diretivas de rastreamento
├── sitemap.xml             # Mapa do site para SEO
├── css/
│   └── styles.css          # CSS responsivo + dark mode
├── js/
│   ├── app.js              # Busca, navegação, TTS, VLibras, criptografia
│   └── sw-register.js      # Registro do Service Worker
├── data/
│   ├── direitos.json       # Base de conhecimento (30 categorias + IPVA inline)
│   ├── matching_engine.json # Keywords e motor de busca
│   └── dicionario_pcd.json  # Dicionário PcD (deficiências, CIDs, leis)
├── images/                 # Favicons, OG image e logo
├── schemas/
│   ├── direitos.schema.json # JSON Schema (Draft 7) para direitos.json
│   ├── matching_engine.schema.json
│   └── dicionario_pcd.schema.json
├── docs/
│   ├── ARCHITECTURE.md     # Arquitetura completa do sistema
│   ├── ARCHITECTURE.drawio.xml # Diagrama visual (draw.io)
│   ├── ACCESSIBILITY.md    # WCAG/eMAG, correções, widgets
│   ├── COMPLIANCE.md       # LGPD, LBI, ISO, Azure
│   ├── CONTRIBUTING.md     # Guia de contribuição
│   ├── KNOWN_ISSUES.md     # Bugs, VLibras, limitações
│   ├── QUALITY_GUIDE.md    # Quick Start, pipeline, scripts, testes
│   └── REFERENCE.md        # 31+ benefícios PcD, dependências
├── tests/
│   ├── test_comprehensive.py           # Testes unitários abrangentes
│   ├── test_comprehensive_validation.py # Validação completa de dados
│   ├── test_cross_browser.py           # Compatibilidade cross-browser
│   ├── test_e2e_playwright.py          # Testes E2E (Playwright)
│   ├── test_master_compliance.py       # Validação de compliance
│   └── conftest.py                     # Fixtures compartilhadas
├── scripts/
│   ├── master_compliance.py # Compliance 360° (21 categorias, score 100%)
│   ├── validate_all.py     # Quality Gate agregado (--quick)
│   ├── validate_content.py # Validação de conteúdo JSON
│   ├── validate_schema.py  # Validação JSON Schema
│   ├── validate_sources.py # Validação de fontes oficiais
│   ├── validate_urls.py    # URLs gov.br + whitelist de domínios
│   ├── validate_legal_compliance.py # Auditoria legal profunda
│   ├── validate_legal_sources.py # Extração de artigos de leis
│   ├── analise360.py       # Análise 360° de cobertura
│   ├── audit_automation.py # Auditoria de automação
│   ├── complete_beneficios.py # Auto-completar benefícios
│   ├── discover_benefits.py # Descob. de benefícios gov.br
│   ├── bump_version.py     # Semver automático
│   └── pre-commit          # Hook de pré-commit
├── terraform/              # Infraestrutura como código
│   ├── main.tf             # App Service + Key Vault + SSL
│   ├── variables.tf        # Variáveis multi-ambiente
│   ├── outputs.tf          # Outputs pós-apply
│   └── providers.tf        # Provider azurerm ~>4.0
├── .github/workflows/
│   ├── deploy.yml              # CI/CD push → deploy Azure
│   ├── quality-gate.yml        # Quality Gate PR/push check
│   ├── discover-benefits.yml   # Descoberta de benefícios gov.br
│   ├── dependabot-auto-merge.yml # Auto-merge Dependabot PRs
│   ├── terraform.yml           # IaC manual dispatch
│   └── weekly-review.yml       # Issue automática periódica
├── CHANGELOG.md
├── GOVERNANCE.md
├── SECURITY.md
├── SECURITY_AUDIT.md
├── LICENSE
└── README.md
```

## 🚀 Instalação e uso local

```bash
cd nossodireito
node server.js
# ou simplesmente:
python -m http.server 8000
```

Acesse `http://localhost:8080` (Node) ou `http://localhost:8000` (Python)

## ⚠️ Aviso Legal

Este site é um **guia informacional** e **NÃO constitui**:

- Assessoria ou consultoria jurídica
- Orientação médica ou de saúde
- Substituição a profissionais qualificados

As informações são compiladas de **fontes oficiais** do governo brasileiro (gov.br) e podem estar desatualizadas. **Sempre verifique as fontes originais** e consulte profissionais qualificados.

**Para orientação profissional gratuita:** procure a **Defensoria Pública** ou o **CRAS** da sua cidade.

## 📚 Principais leis referenciadas

- [Lei 8.742/1993 (LOAS)](https://www.planalto.gov.br/ccivil_03/leis/l8742.htm)
- [Lei 12.764/2012 (Berenice Piana — TEA)](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12764.htm)
- [Lei 13.146/2015 (Estatuto da Pessoa com Deficiência)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm)
- [Lei 13.977/2020 (Romeo Mion — CIPTEA)](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l13977.htm)
- [Lei 13.709/2018 (LGPD)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

## 📄 Licença

MIT — Código livre para reutilização. As informações legais são de domínio público.

## 🏷️ Aviso sobre Marcas

Este é um projeto **open source, gratuito e sem fins lucrativos**, de caráter exclusivamente **educacional e informativo**. **NÃO presta, oferece ou comercializa serviços jurídicos** de qualquer natureza. Não possui vínculo com escritórios de advocacia, lawtechs ou entidades que prestem serviços jurídicos. O nome "NossoDireito" identifica exclusivamente este software de código aberto. Marcas registradas mencionadas pertencem aos seus respectivos titulares.

---

_Feito com 💙 para as famílias que precisam de informação acessível._
