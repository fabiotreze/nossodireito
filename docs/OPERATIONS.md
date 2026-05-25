# Operations Runbook

**Version:** 1.34.0
**Updated:** 2026-05-24

## Scope

- App runtime: Azure App Service (`app-nossodireito-br`)
- AI endpoint: `/api/analyze-document` with Azure OpenAI (`gpt-4o-mini`)
- OpenAI network mode: Private Endpoint + Private DNS (`privatelink.openai.azure.com`)
- IaC: Terraform in [terraform/](../terraform)

## Daily Checks

1. Check app health:
   - `curl -s https://nossodireito.fabiotreze.com/health | jq`
   - Verify `localAnalysisAvailable=true` and inspect `ai.circuitOpen` / `ai.retryAfterSeconds`.
2. Validate ingress hardening:
   - `curl -s -o /dev/null -w "%{http_code}\n" https://nossodireito.fabiotreze.com/`
   - `curl -s -o /dev/null -w "%{http_code}\n" https://app-nossodireito-br.azurewebsites.net/`
   - Expected: custom domain `200`, direct hostname `403`.
3. Validate security headers:
   - `bash scripts/security_headers_check.sh`
4. Validate tests:
   - `python -m pytest tests/ --ignore=tests/test_e2e_playwright.py -q`
5. Validate Terraform:
   - `cd terraform && terraform fmt -check -recursive && terraform validate`

## Deploy

1. Infrastructure:
   - `gh workflow run terraform.yml -R fabiotreze/nossodireito -f action=apply`
2. App package deploy:
   - `gh workflow run deploy.yml -R fabiotreze/nossodireito`
3. Post-deploy smoke:
   - `curl -s https://nossodireito.fabiotreze.com/ | grep -E "aiConsentRevokeInline|v=1.21.0"`

## Incident Triage

1. Confirm Azure app is running:
   - `az webapp show -n app-nossodireito-br -g rg-nossodireito-br --query state -o tsv`
2. Query App Insights (24h failures):
   - `az monitor app-insights query --app appi-nossodireito-br --analytics-query "requests |`
   - `where timestamp > ago(24h) and success == false | summarize count() by name" -o table`
3. Check AI config:
   - `az webapp config appsettings list -n app-nossodireito-br -g rg-nossodireito-br --query`
   - `"[?contains(name,'OPENAI') || name=='AI_ANALYSIS_ENABLED'].{name:name,value:value}" -o table`
4. Check OpenAI private mode:
   - `az cognitiveservices account show -n cog-nossodireito-br-openai -g rg-nossodireito-br`
   - `--query properties.publicNetworkAccess -o tsv`
   - Expected: `Disabled`
5. Check Key Vault private mode:
   - `az keyvault show -n kv-nossodireito-br -g rg-nossodireito-br --query properties.publicNetworkAccess -o tsv`
   - Expected: `Disabled`
6. Check Redis private mode:
   - `az redis show -n redis-nossodireito-br -g rg-nossodireito-br --query publicNetworkAccess -o tsv`
   - Expected: `Disabled`

## AI Resilience Controls

- `AI_TIMEOUT_MS` (default: `12000`): timeout por chamada IA.
- `AI_MAX_RETRIES` (default: `2`): tentativas adicionais para erros transitórios.
- `AI_RETRY_BASE_MS` (default: `600`): backoff exponencial base.
- `AI_CB_FAILURE_THRESHOLD` (default: `3`): falhas consecutivas para abrir circuit breaker.
- `AI_CB_COOLDOWN_MS` (default: `60000`): janela de cooldown do circuit breaker.

Quando o circuit breaker está aberto, `/api/analyze-document` responde `503`
com `Retry-After` e o frontend mantém a análise local como fallback padrão.

## Change Control

- Use branch + PR by default for large changes.
- Keep `main` deployable and version-consistent (`package.json`, `data/*.json`, `sw.js`, cache-bust in `index.html`).
- Never commit `terraform/terraform.tfvars` or certificate files.
- In runner fora da VNet, manter `manage_redis_secret_with_terraform=false` para evitar erro 403 no refresh de segredo em Key Vault privado.
