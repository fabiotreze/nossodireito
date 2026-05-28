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
[![Version](https://img.shields.io/github/v/tag/fabiotreze/nossodireito?style=flat-square&label=version)](https://github.com/fabiotreze/nossodireito/releases)
[![Quality Gate](https://github.com/fabiotreze/nossodireito/actions/workflows/quality-gate.yml/badge.svg)](https://github.com/fabiotreze/nossodireito/actions/workflows/quality-gate.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/fabiotreze/nossodireito/quality-gate.yml?label=tests&style=flat-square&logo=pytest)](docs/OPERATIONS.md)
[![CodeQL](https://github.com/fabiotreze/nossodireito/actions/workflows/codeql.yml/badge.svg)](https://github.com/fabiotreze/nossodireito/actions/workflows/codeql.yml)
[![gitleaks](https://github.com/fabiotreze/nossodireito/actions/workflows/gitleaks.yml/badge.svg)](https://github.com/fabiotreze/nossodireito/actions/workflows/gitleaks.yml)
[![npm audit](https://img.shields.io/badge/npm%20audit-0%20vulnerabilities-brightgreen?style=flat-square&logo=npm)](package.json)

**Recebeu um laudo? Vem que a gente te ajuda.**

Guia gratuito, sem fins lucrativos, com direitos, benefícios e passo a passo para famílias de pessoas com deficiência (PcD) no Brasil.

🌐 **[nossodireito.fabiotreze.com](https://nossodireito.fabiotreze.com)**

O site continua público para o usuário final, mas o App Service aceita tráfego direto apenas da Cloudflare; o restante da comunicação do app com Azure segue por Private Endpoint e VNet.

O Key Vault agora roda em modo privado por padrão; o apply do Terraform precisa acontecer a partir de um contexto com acesso à VNet para operações de data-plane (ex.: importar PFX e leitura/escrita de segredos).

Por padrão, o segredo `redis-primary-key` não é mais gerenciado pelo Terraform (`manage_redis_secret_with_terraform=false`) para evitar erro 403 em runners fora da VNet quando o Key Vault está fechado.

Arquitetura atualizada (incluindo Mermaid e referências Terraform): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📖 Descrição

**NossoDireito** é um guia digital gratuito que centraliza informações sobre direitos, benefícios e procedimentos para pessoas com deficiência (PcD) no Brasil. Desenvolvido com base exclusivamente em **fontes oficiais do governo brasileiro**, o projeto utiliza tecnologia moderna para tornar informações complexas acessíveis a todos.

Quando uma família recebe um laudo médico de deficiência — seja TEA (Transtorno do Espectro Autista), síndrome de Down, deficiência física, visual, auditiva ou intelectual — surge a pergunta: **"E agora? Quais são nossos direitos?"**

Este projeto responde essa pergunta de forma clara, objetiva e validada.

<!-- ABOUT-EN:START -->
### 🌐 About (English)

**NossoDireito — Rights Portal for People with Disabilities.** Regional project — interface and content in Portuguese (pt-BR) for Brazilian citizens. Web portal with **42 rights categories**, official-source references, keyword-based document analysis, accessibility tools (VLibras sign language, TTS, high contrast, font scaling), and encrypted client-side storage via Web Crypto API (AES-GCM-256). **Zero personal data collection (LGPD compliant).** CI quality gates: CodeQL, gitleaks, Quality Gate (`scripts/validate_all.py`), Lighthouse (perf/seo/a11y/bp) and axe-core WCAG 2.1 AA in 3 browser engines (chromium/firefox/webkit). Deployed to Azure App Service (region `brazilsouth`) via ZIP deploy; Terraform for infrastructure replication.
<!-- ABOUT-EN:END -->

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

## 📘 Documentação consolidada (v1.34.2)

- [`docs/README.md`](docs/README.md) — índice da documentação
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — arquitetura e diagrama E2E
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md) — operação e runbook
- [`docs/SECURITY-LGPD.md`](docs/SECURITY-LGPD.md) — baseline de segurança e LGPD

---

## � Estado atual (v1.34.2)

Após o big-bang cleanup (#170) e a modularização do `server.js` (Onda 7, PRs #179–#182), o repositório é deliberadamente enxuto. **A documentação descreve apenas o que realmente existe no main**, e dois guards de CI impedem regressão:

- [`scripts/check_doc_links.mjs`](scripts/check_doc_links.mjs) — falha se README/docs apontarem para arquivos inexistentes.
- [`scripts/check_docs_truth.mjs`](scripts/check_docs_truth.mjs) — falha se README/docs voltarem a citar features removidas (Service Worker, master-compliance, scripts em pasta legacy, workflows desativados, etc.). Se a feature for restaurada, o guard automaticamente para de bloquear. <!-- docs-truth: allow -->

### Pipeline de gates ativos

- Quality Gate via [`scripts/validate_all.py`](scripts/validate_all.py) (`--quick` em PR)
- Lighthouse CI (perf ≥ 0.85, a11y ≥ 0.90, bp ≥ 0.90, seo ≥ 0.90) em `index.html` local
- axe-core WCAG 2.1 AA em 3 browser engines (chromium/firefox/webkit)
- CodeQL (Python + JavaScript/TypeScript)
- gitleaks (secret scanning)
- Doc-link + docs-truth guards

### 📚 Documentação:

- [`docs/README.md`](docs/README.md) — índice da documentação
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — arquitetura atual
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md) — runbook e operação
- [`docs/SECURITY-LGPD.md`](docs/SECURITY-LGPD.md) — segurança e LGPD

---

## ✨ Funcionalidades

### 📋 **42 Categorias de Direitos**

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
- Busca por keywords em mapeamento semântico validado (matching engine + dicionário PcD)

### ♿ **Acessibilidade Máxima**

- **50+ atributos ARIA** (WCAG 2.1 AA/AAA)
- **VLibras** integrado (tradução em Libras do governo federal)
- **Leitura em voz alta** (Web Speech API nativa)
- **Ajuste de fonte** (aumentar/diminuir)
- **Modo alto contraste**
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
- Última atualização: 18 de maio de 2026
- Revisões periódicas

---

## 🚀 Como Usar

### Para Usuários

1. **Acesse** [nossodireito.fabiotreze.com](https://nossodireito.fabiotreze.com)
2. **Busque** pelo benefício ou digite palavras-chave (ex: "autismo", "isenção de imposto", "escola")
3. **Navegue** pelos resultados e clique no benefício desejado
4. **Leia** requisitos, documentos necessários e passo a passo
5. **Ative acessibilidade** (VLibras, voz, contraste) conforme necessidade

### Para Desenvolvedores

```bash
# Clone o repositório
git clone https://github.com/fabiotreze/nossodireito.git
cd nossodireito

# Instale Python (se necessário para validação)
python3 --version  # Requer 3.10+

# Execute Quality Gate (rápido)
python3 scripts/validate_all.py --quick

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

### **Dados**

- **JSON** — direitos.json (42 categorias, ~400KB) + matching_engine.json (~110KB) + dicionario_pcd.json (~62KB) + municipios_br.json (~340KB)
- **Compressão** — Minificação de HTML/CSS/JS

### **Infraestrutura (IaC)**

- **Terraform** — Provisionamento automático Azure
- **Azure App Service** — Hospedagem (Linux, Node.js 22 LTS)
- **Azure Blob Storage** — Armazenamento de assets
- **GitHub Actions** — CI/CD automatizado

### **Validação e Qualidade**

- **Python 3.10+** — Scripts de validação
- **validate_all.py** — Quality Gate agregado (entry-point único, modo `--quick` no CI)
- **validate_content.py** — verificações de conteúdo JSON
- **validate_schema.py** — JSON Schema (Draft 7)
- **validate_sources.py** — HTTP status das fontes oficiais
- **validate_legal_sources.py** — extração de artigos das leis citadas
- **validate_legal_compliance.py** — auditoria legal profunda
- **Pre-commit Hook** — validação automática antes de cada commit

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
- **sitemap.xml** publicado para a home
- **robots.txt** configurado
- **Schema.org** markup (FAQPage, BreadcrumbList, Article)
- **Pré-render estático opcional**: [`scripts/prerender_direitos.py`](scripts/prerender_direitos.py) gera páginas SEO em `direitos/<slug>/index.html` a partir de `data/direitos.json`. Os arquivos gerados ficam em `.gitignore` e **não são publicados pelo deploy atual** — restaurar requer ligar o passo no `deploy.yml` e regenerar o sitemap.
- **Performance** Lighthouse 95+

## ♿ Acessibilidade

- **🔊 Ouvir** — Leitura em voz alta (Web Speech API nativa, sem dependência)
- **🤟 Libras** — Tradução em Libras via VLibras (governo federal)
- **A± Fonte** — Ajuste de tamanho de fonte
- **🔲 Contraste** — Modo alto contraste

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
├── index.html              # SPA single-file (UI + lógica de consulta)
├── server.js               # Bootstrap do servidor (wiring das libs)
├── package.json            # Dependências (Azure SDKs, openai, redis)
├── robots.txt
├── sitemap.xml
├── css/styles.css
├── js/app.js               # Busca, navegação, TTS, VLibras, criptografia
├── data/
│   ├── direitos.json
│   ├── matching_engine.json
│   ├── dicionario_pcd.json
│   └── municipios_br.json
├── schemas/                # JSON Schemas (Draft 7) dos arquivos data/
├── lib/                    # Módulos extraídos do server.js (Onda 7)
│   ├── mime.js
│   ├── security-headers.js
│   ├── file-resolver.js
│   ├── analytics.js
│   ├── rate-limit.js
│   ├── redis-client.js
│   ├── ai-analyze.js
│   ├── govbr-proxy.js
│   └── infra-handlers.js
├── docs/
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── OPERATIONS.md
│   ├── SECURITY-LGPD.md
│   └── diagrams/           # *.drawio
├── tests/                  # pytest + node:test
├── scripts/
│   ├── validate_all.py             # Quality Gate agregado (--quick)
│   ├── validate_content.py
│   ├── validate_schema.py
│   ├── validate_sources.py
│   ├── validate_legal_compliance.py
│   ├── validate_legal_sources.py
│   ├── prerender_direitos.py       # SSG opcional (não usado no deploy atual)
│   ├── a11y_audit.mjs
│   ├── security_headers_check.sh
│   ├── setup-hooks.mjs
│   ├── check_doc_links.mjs         # Guard de links 404 em docs
│   └── check_docs_truth.mjs        # Guard de drift de docs
├── terraform/                      # IaC (App Service, KV, Redis, OpenAI, VNet)
├── .github/workflows/              # 9 workflows ativos (deploy, quality-gate,
│                                   #   codeql, gitleaks, lighthouse, accessibility,
│                                   #   link-check, terraform, dependabot-auto-merge)
├── GOVERNANCE.md
├── CONTRIBUTING.md
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
