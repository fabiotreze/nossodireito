# Runbook de Operações

**Versão:** 1.39.0

## Escopo

- Runtime: Azure App Service (app-nossodireito-br)
- Infra: Terraform em [terraform/](../terraform)
- Qualidade: workflows em [.github/workflows/](../.github/workflows)

## Rotina diária

1. Saúde da aplicação
   - `curl -s https://nossodireito.fabiotreze.com/health | jq`
2. Ingresso (hardening)
   - `curl -s -o /dev/null -w "%{http_code}\n" https://nossodireito.fabiotreze.com/`
   - `curl -s -o /dev/null -w "%{http_code}\n" https://app-nossodireito-br.azurewebsites.net/`
   - Esperado: custom domain = 200, hostname direto = 403
3. Headers de segurança
   - `bash scripts/security_headers_check.sh`
4. Testes rápidos
   - `python -m pytest tests/ --ignore=tests/test_e2e_playwright.py -q`
   - `npm run test:js`

## Deploy

- Infraestrutura: `gh workflow run terraform.yml -R fabiotreze/nossodireito -f action=apply`
- Aplicação: deploy roda automaticamente em push na main via [deploy.yml](../.github/workflows/deploy.yml)
- Smoke pós deploy:
  - `curl -s https://nossodireito.fabiotreze.com/health | jq`

## Incidentes

1. Estado do app:
   - `az webapp show -n app-nossodireito-br -g rg-nossodireito-br --query state -o tsv`
2. Falhas 24h no App Insights:
   - `az monitor app-insights query --app appi-nossodireito-br --analytics-query "requests | where timestamp > ago(24h) and success == false | summarize count() by name" -o table`
3. OpenAI em modo privado:
   - `az cognitiveservices account show -n cog-nossodireito-br-openai -g rg-nossodireito-br --query properties.publicNetworkAccess -o tsv`
4. Key Vault em modo privado:
   - `az keyvault show -n kv-nossodireito-br -g rg-nossodireito-br --query properties.publicNetworkAccess -o tsv`

## SEO Pilot

- Controle de modo: variável `SEO_PRERENDER_MODE`
  - `home-only` (padrão seguro)
  - `prerender` (piloto)
- Watchdog: [seo-pilot-watchdog.yml](../.github/workflows/seo-pilot-watchdog.yml)
  - monitora falhas de CI/deploy em 24h
  - integra opcionalmente com GSC

### Secrets para GSC (opcional)

- `GSC_PROPERTY_URL`
- `GSC_OAUTH_CLIENT_ID`
- `GSC_OAUTH_CLIENT_SECRET`
- `GSC_OAUTH_REFRESH_TOKEN`

Sem esses secrets, o watchdog continua válido para monitorar CI/deploy.

## Backup e Recuperação de Desastre

### Estado Terraform

- Backend remoto `azurerm` ATIVO desde 2026-05-31 — ver [terraform/BACKEND-REMOTE.md](../terraform/BACKEND-REMOTE.md).
- Storage: `stnossodireitobr` / container `tfstate` / blob `nossodireito.prod.tfstate`.
- Lock nativo via blob lease (não há mais corrida entre runs paralelos).
- Auth: Azure AD (RBAC `Storage Blob Data Contributor` no SA) — não há chave compartilhada.
- Recuperação: blob versioning + soft-delete do SA permitem `az storage blob undelete` em até 7 dias.

### Telemetria de longo prazo (Marco Civil + LGPD Art. 16)

- Data Export `export-appi-to-storage` envia continuamente as tabelas
  `AppRequests`, `AppTraces`, `AppExceptions`, `AppDependencies`,
  `AppCustomEvents` do workspace `log-nossodireito-br` para o container
  `appi-logs` no SA `stnossodireitobr`.
- Permite reter logs além dos 30 dias do App Insights por custo Cool tier.
- Consulta: `az storage blob list -c appi-logs --account-name stnossodireitobr --auth-mode login -o table`.

### Key Vault (segredos)

- Soft-delete: 7 dias (imutável após criação).
- Purge-protection: **ATIVO** (segredos deletados não podem ser purgados antes do prazo).
- Restore: `az keyvault secret recover --vault-name kv-nossodireito-br --name <secret>`.

### Aplicação

- Backup do filesystem do App Service: não há (stateless — código vem do repo Git, dados vêm de Azure OpenAI e do navegador).
- Recuperação: redeploy a partir da última tag estável (`gh workflow run deploy.yml --ref v1.39.0`).

### Procedimento de DR completo

1. Reinstanciar infra: `gh workflow run terraform.yml -f action=apply` (lê state do SA).
2. Restaurar segredos via `az keyvault secret recover` se aplicável.
3. Redeploy: push na `main` ou `gh workflow run deploy.yml`.
4. Validar: `curl https://nossodireito.fabiotreze.com/healthz`.

