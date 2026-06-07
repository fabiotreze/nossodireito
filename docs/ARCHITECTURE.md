# Arquitetura Atual — NossoDireito

**Versão:** 1.43.48
**Atualizado:** 2026-06-07

## Visao Geral

A plataforma roda em Azure App Service Linux (Node.js 22) com entrega via dominio customizado em Cloudflare. O backend expoe conteudo estatico e a API de analise por IA com opt-in explicito, usando Azure OpenAI em modo privado.

## Topologia de Execucao

- Borda: Cloudflare (DNS, CDN, WAF, TLS)
- Aplicacao: Azure App Service (`app-nossodireito-br`)
- Runtime: Node.js 22 LTS
- Regiao: Brazil South (`brazilsouth`)
- Observabilidade: Log Analytics Workspace `log-nossodireito-br` (180d, Marco Civil Art. 13) + 4 metric alerts + 2 KQL alerts.
- Segredos: Azure Key Vault + Managed Identity
- Cache/rate limit: Azure Cache for Redis (TLS 1.2)
- Rede privada: VNet + subnets dedicadas + Private Endpoints
- DNS privado: zonas `privatelink.*` para OpenAI, Key Vault e Redis
- CI/CD: GitHub Actions com OIDC

## Inventario de Infraestrutura (Atual)

- Resource Group: `rg-nossodireito-br`
- App Service Plan: `plan-nossodireito-br` (Linux, B1)
- App Service: `app-nossodireito-br`
- Azure OpenAI: `cog-nossodireito-br-openai` (deployment `gpt-4o-mini`)
- Key Vault: `kv-nossodireito-br`
- Redis: `redis-nossodireito-br`
- VNet: `vnet-nossodireito-br` (`10.42.0.0/16`)
- Subnet App Service Integration: `snet-appsvc-prod` (`10.42.1.0/24`)
- Subnet OpenAI PE: `snet-openai-pe-prod` (`10.42.2.0/24`)
- Subnet Key Vault PE: `snet-kv-pe-prod` (`10.42.3.0/24`)
- Subnet Redis PE: `snet-redis-pe-prod` (`10.42.4.0/24`)

## Diagrama Mermaid (Infra E2E)

```mermaid
flowchart LR
	U[Usuario] --> CF[Cloudflare Edge]
	CF -->|HTTPS 443| APP[App Service app-nossodireito-br]

	subgraph AZ[Azure - brazilsouth]

		subgraph VNET[vnet-nossodireito-br 10.42.0.0/16]
			APPINT[snet-appsvc-prod 10.42.1.0/24]
			OPEP[snet-openai-pe-prod 10.42.2.0/24]
			KPEP[snet-kv-pe-prod 10.42.3.0/24]
			RPEP[snet-redis-pe-prod 10.42.4.0/24]
		end

		APP -.VNet Integration.-> APPINT
		APP -->|MSI + Private DNS| KV[Key Vault kv-nossodireito-br]
		APP -->|TLS 6380 + Secret no KV| REDIS[Redis redis-nossodireito-br]
		APP -->|Private Endpoint| OAI[Azure OpenAI gpt-4o-mini]

		OPEP --> OAI
		KPEP --> KV
		RPEP --> REDIS

		PDNSO[privatelink.openai.azure.com]
		PDNSK[privatelink.vaultcore.azure.net]
		PDNSR[privatelink.redis.cache.windows.net]

		APP --> PDNSO
		APP --> PDNSK
		APP --> PDNSR
	end

	CF -.somente IPs Cloudflare permitidos no App Service.-> APP
	APP -.hostname direto azurewebsites bloqueado.-> BLOCK[HTTP 403 esperado]
```

## Fluxo de Requisicao

1. Usuario acessa `https://nossodireito.fabiotreze.com`.
2. Cloudflare aplica protecao de borda e encaminha para App Service.
3. O App Service entrega a UI estática e os ativos versionados.
4. Em analise por IA, o frontend exige consentimento explicito.
5. O backend anonimiza o texto e chama Azure OpenAI via Private Endpoint.
6. A resposta volta para o cliente sem persistencia de dados pessoais no servidor.

## API e Endpoints

- `GET /` -> aplicacao web
- `GET /health` -> health check da aplicacao
- `POST /api/analyze-document` -> analise de texto com IA (opt-in)
- `GET /data/*.json` -> base de direitos e mecanismos de busca

## SEO

A SPA usa hash-routing internamente. O sitemap publicado atualmente lista apenas a home; `scripts/prerender_direitos.py` pode gerar páginas profundas em `direitos/<slug>/index.html` a partir de `data/direitos.json`, mas os arquivos gerados ficam em `.gitignore` e o `deploy.yml` não executa o pré-render — portanto, hoje, não há páginas SEO por categoria em produção. Restaurar requer: rodar o script, ajustar o sitemap e ligar o passo no workflow de deploy.

`server.js` resolve URLs limpas via `resolveFile`: requisições sem extensão tentam `<path>/index.html` -> `<path>.html` -> fallback SPA.

## Privacidade e LGPD

- Coleta de dados pessoais: nao
- Consentimento para IA: obrigatorio, especifico e revogavel
- Revogacao de consentimento: disponivel permanentemente na interface
- Base legal da analise de IA: consentimento (LGPD Art. 7o, I)
- Tratamento: anonimizado antes de envio ao provedor de IA

## Seguranca Aplicada

- HTTPS obrigatorio
- Security headers no servidor (CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy)
- Rate limiting para endpoint de IA
- Managed Identity para acesso a recursos Azure
- App Service com allowlist de IPs Cloudflare e default deny
- OpenAI, Key Vault e Redis com conectividade privada
- Sem secrets de producao hardcoded no codigo

## Observacoes de Operacao

- O hostname direto do App Service (`*.azurewebsites.net`) deve retornar 403 por hardening.
- O endpoint publico oficial e o dominio customizado em Cloudflare.
- O Key Vault roda privado por padrao (`public_network_access_enabled=false`).
- O segredo `redis-primary-key` permanece como referencia de app setting, mas por padrao nao e gerenciado via Terraform (`manage_redis_secret_with_terraform=false`) para evitar falha de data-plane em runners fora da VNet.

## Observabilidade

- Log Analytics Workspace: `log-nossodireito-br` (PerGB2018, retenção `180` dias — Marco Civil Art. 13).
- Diagnostic settings ativos (definidos em [terraform/observability.tf](../terraform/observability.tf)):
  - App Service: `AppServiceHTTPLogs`, `AppServiceConsoleLogs`, `AppServiceAppLogs`, `AppServiceAuditLogs`, `AppServiceIPSecAuditLogs`, `AppServicePlatformLogs` + `AllMetrics`.
  - Key Vault: `AuditEvent`, `AzurePolicyEvaluationDetails` + `AllMetrics` (count `var.enable_keyvault`).
  - Azure OpenAI: `Audit`, `RequestResponse` (sem corpo de prompt/completion) + `AllMetrics` (count `var.enable_ai_openai`).
  - Redis: `AllMetrics` apenas (SKU Basic não expõe categorias de log).
- Action group: `ag-nossodireito-email` (destino: `fabiotreze@gmail.com`).
- Alertas de métrica (severidades S0–S3):
  - `alert-app-nossodireito-br-5xx` — Http5xx > 0 (S1).
  - `alert-app-nossodireito-br-health` — HealthCheckStatus < 100 (S0).
  - `alert-app-nossodireito-br-latency` — HttpResponseTime > 5s (S2).
  - `alert-app-nossodireito-br-4xx` — Http4xx > 50 em 5min (S3).
- Alertas KQL (defesa em profundidade):
  - `alert-cloudflare-bypass` — requisições no App Service vindas de IP fora das faixas Cloudflare (S2).
  - `alert-kv-denied-access` — tentativas de acesso negadas (Forbidden/Unauthorized) ao Key Vault (S1).

## Gates de Qualidade (CI/CD)

Todo PR para `main` precisa passar nos checks abaixo (configurado em branch protection):

| Check                                       | Ferramenta                              | Bloqueia? |
| ------------------------------------------- | --------------------------------------- | --------- |
| `CodeQL`                                    | GitHub Code Scanning (py + js/ts)       | sim       |
| `gitleaks scan`                             | gitleaks                                | sim       |
| `Quality Gate`                              | `scripts/validate_all.py --quick`       | sim       |
| `Lighthouse (perf/seo/a11y/bp)`             | `@lhci/cli` + `lighthouserc.json`       | sim       |
| `A11y (axe-core WCAG 2.1 AA) (chromium)`    | `tests/a11y.mjs` + Playwright           | sim       |
| `A11y (axe-core WCAG 2.1 AA) (firefox)`     | `tests/a11y.mjs` + Playwright           | sim       |
| `A11y (axe-core WCAG 2.1 AA) (webkit)`      | `tests/a11y.mjs` + Playwright           | sim       |
| `Doc-link guard`                            | `scripts/check_doc_links.mjs`           | sim       |
| `Docs-truth guard`                          | `scripts/check_docs_truth.mjs`          | sim       |

Thresholds atuais (Lighthouse): perf ≥ 0.85, a11y ≥ 0.90, best-practices ≥ 0.90, seo ≥ 0.90. URL auditada: `index.html` servido localmente pelo Lighthouse CI.

## Diagramas

- Fluxo de IA: [diagrams/02-ia-flow.md](diagrams/02-ia-flow.md) (Mermaid sequence)
- Replicacao / Deploy: [diagrams/03-replication.md](diagrams/03-replication.md) (Mermaid flowchart)

## Referencias de Infra (Terraform)

- [terraform/main.tf](../terraform/main.tf)
- [terraform/openai-private-network.tf](../terraform/openai-private-network.tf)
- [terraform/keyvault-redis-private-network.tf](../terraform/keyvault-redis-private-network.tf)
- [terraform/observability.tf](../terraform/observability.tf)
- [terraform/variables.tf](../terraform/variables.tf)
- [terraform/outputs.tf](../terraform/outputs.tf)
- [terraform/providers.tf](../terraform/providers.tf) — backend remoto `azurerm` (state em `stnossodireitobr/tfstate`)
- [terraform/BACKEND-REMOTE.md](../terraform/BACKEND-REMOTE.md) — guia operacional do state remoto

## Referencias Operacionais

- Operacao e runbook: [OPERATIONS.md](OPERATIONS.md)
- Seguranca e LGPD: [SECURITY-LGPD.md](SECURITY-LGPD.md)
