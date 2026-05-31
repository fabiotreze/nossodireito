<p align="center">
  <img src="images/nossodireito-400.webp" alt="NossoDireito" width="120">
</p>

# ⚖️ NossoDireito

[![Compliance](https://img.shields.io/badge/Compliance-LGPD%20Current%20State-brightgreen?style=flat-square)](docs/SECURITY-LGPD.md)
[![Azure WAF](https://img.shields.io/badge/Azure%20WAF-Aligned-success?style=flat-square&logo=microsoftazure)](docs/ARCHITECTURE.md)
[![Security](https://img.shields.io/badge/Security-HTTPS%20%7C%20CSP%20%7C%20Zero%20Tracking-green?style=flat-square&logo=letsencrypt)](SECURITY.md)
[![Accessibility](https://img.shields.io/badge/Accessibility-ARIA%20%7C%20VLibras%20%7C%20WCAG-blue?style=flat-square&logo=accessible-icon)](docs/OPERATIONS.md)
[![LGPD](https://img.shields.io/badge/LGPD-Zero%20Data%20Collection-blue?style=flat-square)](docs/SECURITY-LGPD.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/github/package-json/v/fabiotreze/nossodireito?style=flat-square&label=version)](package.json)
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

## Descrição

NossoDireito é um guia gratuito para famílias de pessoas com deficiência no Brasil,
com conteúdo baseado em fontes oficiais e foco em linguagem simples.

<!-- ABOUT-EN:START -->
**NossoDireito — Rights Portal for People with Disabilities.** Regional project — interface and content in Portuguese (pt-BR) for Brazilian citizens. Web portal with **42 rights categories**, official-source references, keyword-based document analysis, accessibility tools (VLibras sign language, TTS, high contrast, font scaling), and encrypted client-side storage via Web Crypto API (AES-GCM-256). **Zero personal data collection (LGPD compliant).** CI quality gates: CodeQL, gitleaks, Quality Gate (`scripts/validate_all.py`), Lighthouse (perf/seo/a11y/bp) and axe-core WCAG 2.1 AA in 3 browser engines (chromium/firefox/webkit). Deployed to Azure App Service (region `brazilsouth`) via ZIP deploy; Terraform (azurerm remote state) for infrastructure replication.
<!-- ABOUT-EN:END -->

## Quick Start

```bash
git clone https://github.com/fabiotreze/nossodireito.git
cd nossodireito

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
# python -m venv .venv
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt -r requirements-dev.txt
npm ci
node server.js
```

Acesse: http://localhost:8080

## Operação e Deploy

- Runbook de operação: [docs/OPERATIONS.md](docs/OPERATIONS.md)
- Arquitetura e infraestrutura: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Segurança e LGPD: [docs/SECURITY-LGPD.md](docs/SECURITY-LGPD.md)
- Índice completo de docs: [docs/README.md](docs/README.md)

## Qualidade

Pipeline principal de qualidade no CI:

- Quality Gate
- Lighthouse CI
- Acessibilidade (axe-core)
- CodeQL
- gitleaks

Validação local rápida:

```bash
python3 scripts/validate_all.py --quick
npm run test:js
```

## SEO

- Modo controlado por variável: SEO_PRERENDER_MODE
- Valores aceitos: home-only ou prerender
- Geração estática: [scripts/prerender_direitos.py](scripts/prerender_direitos.py)

## Aviso Legal

Este projeto é informativo e não substitui orientação jurídica ou médica.
Sempre confirme requisitos e regras nas fontes oficiais.

## Licença

[MIT](LICENSE)
