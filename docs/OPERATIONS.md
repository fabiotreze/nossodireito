## Operations Runbook

**Version:** 1.19.0
**Updated:** 2026-05-18

## Scope

- App runtime: Azure App Service (`app-nossodireito-br`)
- AI endpoint: `/api/analyze-document` with Azure OpenAI (`gpt-4o-mini`)
- IaC: Terraform in [terraform/](../terraform)

## Daily Checks

1. Check app health:
   - `curl -sI https://app-nossodireito-br.azurewebsites.net/`
2. Validate security headers:
   - `bash scripts/security_headers_check.sh`
3. Validate tests:
   - `python -m pytest tests/ --ignore=tests/test_e2e_playwright.py -q`
4. Validate Terraform:
   - `cd terraform && terraform fmt -check -recursive && terraform validate`

## Deploy

1. Infrastructure:
   - `gh workflow run terraform.yml -R fabiotreze/nossodireito -f action=apply`
2. App package deploy:
   - `gh workflow run deploy.yml -R fabiotreze/nossodireito`
3. Post-deploy smoke:
   - `curl -s https://app-nossodireito-br.azurewebsites.net/ | grep -E "aiConsentRevokeInline|v=1.19.0"`

## Incident Triage

1. Confirm Azure app is running:
   - `az webapp show -n app-nossodireito-br -g rg-nossodireito-br --query state -o tsv`
2. Query App Insights (24h failures):
   - `az monitor app-insights query --app appi-nossodireito-br --analytics-query "requests | where timestamp > ago(24h) and success == false | summarize count() by name" -o table`
3. Check AI config:
   - `az webapp config appsettings list -n app-nossodireito-br -g rg-nossodireito-br --query "[?contains(name,'OPENAI') || name=='AI_ANALYSIS_ENABLED'].{name:name,value:value}" -o table`

## Change Control

- Use branch + PR by default for large changes.
- Keep `main` deployable and version-consistent (`package.json`, `data/*.json`, `sw.js`, cache-bust in `index.html`).
- Never commit `terraform/terraform.tfvars` or certificate files.
