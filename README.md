<p align="center">
  <img src="images/nossodireito-400.webp" alt="NossoDireito" width="120">
</p>

# ⚖️ NossoDireito

[![Compliance](https://img.shields.io/badge/Compliance-LGPD%20Current%20State-brightgreen?style=flat-square)](docs/SECURITY-LGPD.md)
[![Security](https://img.shields.io/badge/Security-HTTPS%20%7C%20CSP%20%7C%20Zero%20Tracking-green?style=flat-square&logo=letsencrypt)](SECURITY.md)
[![Accessibility](https://img.shields.io/badge/Accessibility-ARIA%20%7C%20VLibras%20%7C%20WCAG-blue?style=flat-square&logo=accessible-icon)](SECURITY.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/github/package-json/v/fabiotreze/nossodireito?style=flat-square&label=version)](package.json)
[![Quality Gate](https://github.com/fabiotreze/nossodireito/actions/workflows/quality-gate.yml/badge.svg)](https://github.com/fabiotreze/nossodireito/actions/workflows/quality-gate.yml)
[![CodeQL](https://github.com/fabiotreze/nossodireito/actions/workflows/codeql.yml/badge.svg)](https://github.com/fabiotreze/nossodireito/actions/workflows/codeql.yml)
[![gitleaks](https://github.com/fabiotreze/nossodireito/actions/workflows/gitleaks.yml/badge.svg)](https://github.com/fabiotreze/nossodireito/actions/workflows/gitleaks.yml)

**Catálogo público de direitos PcD com referências às fontes oficiais brasileiras.**

Reunimos leis, portarias e canais oficiais (.gov.br, Planalto, INSS, Ministério da Saúde) em um só lugar — você parte daqui e vai direto à fonte. Não interpretamos a lei, não orientamos casos individuais.

🌐 **[nossodireito.fabiotreze.com](https://nossodireito.fabiotreze.com)**

O site continua público para o usuário final, mas o App Service aceita tráfego direto apenas da Cloudflare; o restante da comunicação do app com Azure segue por Private Endpoint e VNet.

O Key Vault agora roda em modo privado por padrão; o apply do Terraform precisa acontecer a partir de um contexto com acesso à VNet para operações de data-plane (ex.: importar PFX e leitura/escrita de segredos).

Por padrão, o segredo `redis-primary-key` não é mais gerenciado pelo Terraform (`manage_redis_secret_with_terraform=false`) para evitar erro 403 em runners fora da VNet quando o Key Vault está fechado.

Arquitetura atualizada (incluindo Mermaid e referências Terraform): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Descrição

NossoDireito é um catálogo público que reúne referências a fontes oficiais brasileiras sobre direitos
de pessoas com deficiência. Cada conteúdo cita explicitamente a base legal e o canal oficial — o
usuário lê direto da fonte. Não interpretamos a lei, não orientamos casos individuais, não prestamos
serviços jurídicos.

<!-- ABOUT-EN:START -->
**NossoDireito — Public Catalog of Rights for People with Disabilities in Brazil.** Regional project — interface and content in Portuguese (pt-BR) for Brazilian citizens. Public catalog that **references official sources** (.gov.br, Planalto, INSS, Ministry of Health) across **42 rights categories**, with keyword-based document analysis, accessibility tools (VLibras sign language, TTS, high contrast, font scaling), and encrypted client-side storage via Web Crypto API (AES-GCM-256). Does not interpret law, does not advise on individual cases. **Zero personal data collection (LGPD compliant).** CI quality gates: CodeQL, gitleaks, Quality Gate (`scripts/validate_all.py`), Lighthouse (perf/seo/a11y/bp) and axe-core WCAG 2.1 AA in 3 browser engines (chromium/firefox/webkit). Deployed to Azure App Service (region `brazilsouth`) via ZIP deploy; Terraform (azurerm remote state) for infrastructure replication.
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
- Princípios de uso de IA: [docs/AI-PRINCIPLES.md](docs/AI-PRINCIPLES.md) (alinhado a [Microsoft Learn](https://learn.microsoft.com/en-gb/principles-for-ai-generated-content))
- Índice completo de docs: [docs/README.md](docs/README.md)

### Health & observabilidade

- Health-check público: `curl -s https://nossodireito.fabiotreze.com/health | jq` (200 OK + versão + estado da IA).
- Dashboard público: [status.html](status.html) (faz `GET /health` do browser do usuário, sem persistência).
- Logs e métricas: Log Analytics `log-nossodireito-br` (retenção 180 dias — Marco Civil Art. 13).
- Alertas: 4 metric + 2 KQL → action group `ag-nossodireito-email`. Detalhes em [docs/OPERATIONS.md#alertas](docs/OPERATIONS.md#alertas).

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

Este projeto é um catálogo público informativo e não substitui orientação jurídica, médica ou social.
Sempre confirme requisitos e regras nas fontes oficiais linkadas em cada direito.

## Licença

Código-fonte sob licença [MIT](LICENSE).

## Licença de Conteúdo

Conteúdo editorial e informativo (incluindo textos das páginas e documentação em linguagem natural) sob
[Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-CONTENT).

Ao reutilizar esse conteúdo, faça atribuição adequada ao projeto NossoDireito e indique eventuais alterações.
