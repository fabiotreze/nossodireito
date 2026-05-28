# Runbook de Operações

**Versão:** 1.34.2
**Atualizado:** 2026-05-27

## Escopo

- Runtime da aplicação: Azure App Service (`app-nossodireito-br`)
- Endpoint de IA: `/api/analyze-document` com Azure OpenAI (`gpt-4o-mini`)
- Modo de rede do OpenAI: Private Endpoint + Private DNS (`privatelink.openai.azure.com`)
- IaC: Terraform em [terraform/](../terraform)

## Checagens Diárias

1. Verificar saúde da aplicação:
   - `curl -s https://nossodireito.fabiotreze.com/health | jq`
   - Confirmar `localAnalysisAvailable=true` e inspecionar `ai.circuitOpen` / `ai.retryAfterSeconds`.
2. Validar hardening de ingresso:
   - `curl -s -o /dev/null -w "%{http_code}\n" https://nossodireito.fabiotreze.com/`
   - `curl -s -o /dev/null -w "%{http_code}\n" https://app-nossodireito-br.azurewebsites.net/`
   - Esperado: domínio customizado `200`, hostname direto `403`.
3. Validar headers de segurança:
   - `bash scripts/security_headers_check.sh`
4. Validar testes:
   - `python -m pytest tests/ --ignore=tests/test_e2e_playwright.py -q`
5. Validar Terraform:
   - `cd terraform && terraform fmt -check -recursive && terraform validate`

## Deploy

1. Infraestrutura:
   - `gh workflow run terraform.yml -R fabiotreze/nossodireito -f action=apply`
2. Deploy do pacote da aplicação:
   - `gh workflow run deploy.yml -R fabiotreze/nossodireito`
3. Smoke test pós-deploy:
   - `curl -s https://nossodireito.fabiotreze.com/ | grep -E "aiConsentRevokeInline|v=[0-9]+\.[0-9]+\.[0-9]+"`
   - (a versão exata deve bater com `jq -r .version package.json`)

## Triagem de Incidentes

1. Confirmar que a aplicação Azure está rodando:
   - `az webapp show -n app-nossodireito-br -g rg-nossodireito-br --query state -o tsv`
2. Consultar App Insights (falhas em 24h):
   - `az monitor app-insights query --app appi-nossodireito-br --analytics-query "requests |`
   - `where timestamp > ago(24h) and success == false | summarize count() by name" -o table`
3. Verificar configuração de IA:
   - `az webapp config appsettings list -n app-nossodireito-br -g rg-nossodireito-br --query`
   - `"[?contains(name,'OPENAI') || name=='AI_ANALYSIS_ENABLED'].{name:name,value:value}" -o table`
4. Verificar modo privado do OpenAI:
   - `az cognitiveservices account show -n cog-nossodireito-br-openai -g rg-nossodireito-br`
   - `--query properties.publicNetworkAccess -o tsv`
   - Esperado: `Disabled`
5. Verificar modo privado do Key Vault:
   - `az keyvault show -n kv-nossodireito-br -g rg-nossodireito-br --query properties.publicNetworkAccess -o tsv`
   - Esperado: `Disabled`
6. Verificar modo privado do Redis:
   - `az redis show -n redis-nossodireito-br -g rg-nossodireito-br --query publicNetworkAccess -o tsv`
   - Esperado: `Disabled`

## Controles de Resiliência de IA

- `AI_TIMEOUT_MS` (padrão: `12000`): timeout por chamada de IA.
- `AI_MAX_RETRIES` (padrão: `2`): tentativas adicionais para erros transitórios.
- `AI_RETRY_BASE_MS` (padrão: `600`): backoff exponencial base.
- `AI_CB_FAILURE_THRESHOLD` (padrão: `3`): falhas consecutivas para abrir o circuit breaker.
- `AI_CB_COOLDOWN_MS` (padrão: `60000`): janela de cooldown do circuit breaker.

Quando o circuit breaker está aberto, `/api/analyze-document` responde `503`
com `Retry-After` e o frontend mantém a análise local como fallback padrão.

## Controle de Mudanças

- Use branch + PR por padrão para mudanças grandes.
- Mantenha `main` deployável e com versões consistentes (`package.json`, `data/*.json`, cache-bust em `index.html`).
- Nunca commite `terraform/terraform.tfvars` nem arquivos de certificado.
- Em runner fora da VNet, manter `manage_redis_secret_with_terraform=false` para evitar erro 403 no refresh de segredo em Key Vault privado.
