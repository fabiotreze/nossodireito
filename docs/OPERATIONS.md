# Runbook de Operações

**Versão:** 1.43.4

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
2. Falhas 24h (App Service HTTP logs via Log stream):
   - `az webapp log tail -n app-nossodireito-br -g rg-nossodireito-br`
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
- **Recuperação:** blob versioning ATIVO + blob soft-delete 7d + container soft-delete 7d (ligados em 2026-05-31). Permitem `az storage blob undelete` e restore de versões anteriores do state.

### Key Vault (segredos)

- Soft-delete: 7 dias (imutável após criação).
- Purge-protection: **ATIVO** (segredos deletados não podem ser purgados antes do prazo).
- Restore: `az keyvault secret recover --vault-name kv-nossodireito-br --name <secret>`.

### Aplicação

- Backup do filesystem do App Service: não há (stateless — código vem do repo Git, dados vêm de Azure OpenAI e do navegador).
- Recuperação: redeploy a partir da última tag estável (`gh workflow run deploy.yml --ref v1.40.0`).

### Procedimento de DR completo

1. Reinstanciar infra: `gh workflow run terraform.yml -f action=apply` (lê state do SA).
2. Restaurar segredos via `az keyvault secret recover` se aplicável.
3. Redeploy: push na `main` ou `gh workflow run deploy.yml`.
4. Validar: `curl https://nossodireito.fabiotreze.com/health`.

## Evidência de auditoria LGPD / ANPD

Runbook reproduzível para demonstrar conformidade a titular de dado, ANPD ou
auditor. Todos os comandos abaixo são read-only e podem ser executados por
qualquer pessoa com `az login` ativo e papel `Reader` na assinatura
`3acb7300-a8c5-4354-9ad3-0a219a495b4a`.

### Comandos de evidência

```bash
# 1. Ausência de Application Insights / SDK de telemetria no resource group
az resource list -g rg-nossodireito-br \
  --resource-type Microsoft.Insights/components -o table
# Esperado: nenhum resultado (desde 2026-06-05).

# 2. Ausência do pacote applicationinsights nas dependências
grep -E '"applicationinsights"' package.json || echo 'OK: dependência removida'

# 3. Ausência da connection string em runtime
az webapp config appsettings list -g rg-nossodireito-br -n app-nossodireito-br \
  --query "[?name=='APPLICATIONINSIGHTS_CONNECTION_STRING']" -o tsv
# Esperado: vazio

# 4. Key Vault — quem tem acesso
az role assignment list \
  --scope "/subscriptions/3acb7300-a8c5-4354-9ad3-0a219a495b4a/resourceGroups/rg-nossodireito-br/providers/Microsoft.KeyVault/vaults/kv-nossodireito-br" \
  --query "[].{role:roleDefinitionName, principalType:principalType, principalName:principalName}" -o table

# 5. Storage do tfstate — durabilidade (versioning + soft-delete)
az storage account blob-service-properties show \
  --account-name stnossodireitobr -g rg-tfstate-nossodireito \
  --query "{versioning:isVersioningEnabled, blobSoftDelete:deleteRetentionPolicy.days, containerSoftDelete:containerDeleteRetentionPolicy.days}"
```

### Histórico de telemetria (2026-05 — 2026-06-05)

Até 2026-06-05 o portal usava Application Insights via SDK `applicationinsights@3.x` (auto-instrumentação OpenTelemetry). A integração foi **removida por completo** pela impossibilidade de impedir o enrichment server-side de `ClientCity` / `ClientCountryOrRegion` a partir de `client.address`. Registros históricos foram expurgados via Purge API antes da desativação do workspace.

