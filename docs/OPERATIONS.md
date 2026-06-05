# Runbook de Operações

**Versão:** 1.40.0

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
- **Recuperação:** blob versioning ATIVO + blob soft-delete 7d + container soft-delete 7d (ligados em 2026-05-31). Permitem `az storage blob undelete` e restore de versões anteriores do state.

### Telemetria de longo prazo (Marco Civil + LGPD Art. 16)

- Data Export `export-appi-to-storage` envia continuamente as tabelas
  `AppRequests`, `AppTraces`, `AppExceptions`, `AppDependencies`,
  `AppCustomEvents` do workspace `log-nossodireito-br` para o container
  `appi-logs` no SA `stnossodireitobr`.
- Permite reter logs além dos 30 dias do App Insights por custo Cool tier.
- **Retenção máxima:** lifecycle policy `appi-logs-retention-180d` deleta
  blobs do prefixo `appi-logs/` 180 dias após a última modificação
  (cumpre Marco Civil Art. 15 — mínimo 6 meses — e atende LGPD Art. 16
  princípio da necessidade).
- Consulta: `az storage blob list -c appi-logs --account-name stnossodireitobr --auth-mode login -o table`.

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
4. Validar: `curl https://nossodireito.fabiotreze.com/healthz`.

## Evidência de auditoria LGPD / ANPD

Runbook reproduzível para demonstrar conformidade a titular de dado, ANPD ou
auditor. Todos os comandos abaixo são read-only e podem ser executados por
qualquer pessoa com `az login` ativo e papel `Reader` na assinatura
`3acb7300-a8c5-4354-9ad3-0a219a495b4a`.

### Painel visual (Azure Workbook)

- **Nome:** NossoDireito — Painel de Atenção
- **Local:** Azure Portal → Application Insights `appi-nossodireito-br` → Workbooks
- **Conteúdo:** sinais que exigem atenção para LGPD e saúde do portal, contadores de resíduos pessoais, falhas reais (exclui 404/429 esperados), 429 em rotas do portal e info da camada cold.
- **Observação:** o workbook diário não exibe amostra bruta; ele só mostra itens acionáveis. A amostra de não-coleta abaixo serve como evidência complementar do hardening.
- **Fonte versionada:** [terraform/workbooks/lgpd-audit.json](../terraform/workbooks/lgpd-audit.json)

### Comandos de evidência

```bash
# 1. Mascaramento de IP (configuração do App Insights)
az resource show \
  --ids "/subscriptions/3acb7300-a8c5-4354-9ad3-0a219a495b4a/resourceGroups/rg-nossodireito-br/providers/Microsoft.Insights/components/appi-nossodireito-br" \
  --query "properties.DisableIpMasking" -o tsv
# Esperado: false  (masking ATIVO)

# 2. Amostra real do que é gravado — campos sensíveis
az monitor app-insights query --app appi-nossodireito-br -g rg-nossodireito-br \
  --analytics-query "requests | take 20 | project timestamp, name, url, client_IP, client_City, client_CountryOrRegion, user_Id, session_Id"
# Esperado: client_IP="::" (anonimizado), demais vazios

# 3. Tabelas exportadas para a camada cold (não inclui body/payload)
az monitor log-analytics workspace data-export show \
  --workspace-name log-nossodireito-br -g rg-nossodireito-br \
  --name export-appi-to-storage --query tableNames

# 4. Lifecycle policy ativo (LGPD Art. 16 — eliminação após 180 dias)
az storage account management-policy show \
  --account-name stnossodireitobr -g rg-tfstate-nossodireito \
  --query "policy.rules[0]"

# 5. Quem tem acesso aos logs (RBAC)
az role assignment list \
  --scope "/subscriptions/3acb7300-a8c5-4354-9ad3-0a219a495b4a/resourceGroups/rg-tfstate-nossodireito/providers/Microsoft.Storage/storageAccounts/stnossodireitobr" \
  --query "[].{role:roleDefinitionName, principalType:principalType, principalName:principalName}" -o table

# 6. Durabilidade (versioning + soft-delete)
az storage account blob-service-properties show \
  --account-name stnossodireitobr -g rg-tfstate-nossodireito \
  --query "{versioning:isVersioningEnabled, blobSoftDelete:deleteRetentionPolicy.days, containerSoftDelete:containerDeleteRetentionPolicy.days}"
```

### Evidência complementar de anonimização (executado em 2026-05-31)

Saída do comando 2 acima — prova complementar de que **nenhum dado pessoal é coletado**:

```json
[
  {
    "timestamp": "2026-05-31T17:37:12.095Z",
    "name": "GET /health",
    "url": "http://app-nossodireito-br.azurewebsites.net/health",
    "resultCode": "200",
    "client_IP": "::",
    "client_City": "",
    "client_CountryOrRegion": "",
    "user_Id": "",
    "session_Id": ""
  }
]
```

- `client_IP`, `client_City`, `client_CountryOrRegion`, `user_Id`, `session_Id` — vazios após o hardening. Se algum valor surgir, existe coleta residual na origem.
- Demais campos (`timestamp`, `name`, `url`, `resultCode`) são metadados técnicos necessários para operação e não constituem dado pessoal sob LGPD Art. 5º, I.

