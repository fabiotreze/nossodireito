# Fluxo de Replicação / Deploy Atual

**Versão:** 1.43.48
**Atualizado:** 2026-06-07

Pipeline end-to-end de commit → produção, incluindo o ciclo Terraform self-healing e o smoke pós-deploy.

```mermaid
flowchart LR
    DEV[Desenvolvedor] -->|push / PR| GH[GitHub Repo<br/>fabiotreze/nossodireito]

    subgraph CI[GitHub Actions]
        GATE[Quality Gate<br/>validate_all.py + node --test<br/>+ A11y + Lighthouse + CodeQL]
        TF[terraform.yml<br/>plan / apply<br/>auto-import self-healing]
        DEP[deploy.yml<br/>git archive + ZIP]
        WATCH[deploy-watchdog]
    end

    GH --> GATE
    GATE -->|main| TF
    GATE -->|main| DEP

    subgraph AZ[Azure - brazilsouth]
        APP[App Service<br/>app-nossodireito-br]
        KV[Key Vault<br/>kv-nossodireito-br]
        OAI[Azure OpenAI<br/>gpt-4o-mini]
        REDIS[Redis<br/>redis-nossodireito-br]
        LAW[Log Analytics<br/>log-nossodireito-br<br/>180d - Marco Civil Art. 13]
        AG[Action Group<br/>ag-nossodireito-email]
    end

    TF -.OIDC.-> AZ
    DEP -.OIDC + WEBAPP_PUBLISH_PROFILE.-> APP

    APP -->|diag| LAW
    KV -->|diag| LAW
    OAI -->|diag| LAW
    REDIS -->|diag AllMetrics| LAW

    LAW -->|6 alertas<br/>4 metric + 2 KQL| AG
    AG -->|email| OWNER[fabiotreze@gmail.com]

    DEP -->|smoke /health| CF[Cloudflare Edge]
    CF --> APP
    WATCH -->|monitora falhas 24h| GH
```

## Estágios

1. **CI Quality Gate** (`.github/workflows/quality-gate.yml`): validate_all.py + 115 testes JS + axe-core 3 engines + Lighthouse (perf/a11y/bp/seo ≥ 0.85) + CodeQL + gitleaks + `check_docs_truth.mjs` + `check_doc_links.mjs`.
2. **Terraform** (`.github/workflows/terraform.yml`): plan automático em PRs, apply em push para `main`. Auto-import de 10+ recursos garante self-healing após restauração de state ou primeiro run em workspace novo.
3. **Deploy** (`.github/workflows/deploy.yml`): `git archive --worktree-attributes HEAD` (respeita `.gitattributes` export-ignore) → ZIP → `az webapp deploy` via OIDC.
4. **Smoke pós-deploy**: `curl /health` via CDN (informativo, CF pode filtrar GH runners) + retry direto no `*.azurewebsites.net` (validação real).
5. **Observabilidade** (`terraform/observability.tf`): 4 diagnostic settings + 4 metric alerts + 2 KQL alerts → action group → e-mail.
6. **Watchdog** (`.github/workflows/deploy-watchdog.yml`): cron monitora falhas de CI/deploy nas últimas 24h.

## Bootstrap (ambiente novo)

1. `scripts/bootstrap-oidc.sh` cria SP + federated credential GitHub.
2. Secrets configurados: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `ALERT_EMAIL`, `WEBAPP_PUBLISH_PROFILE`.
3. `terraform init` → `terraform apply` provisiona toda a stack.
4. Primeiro deploy via push para `main`.

## Referências

- Workflows: [.github/workflows/terraform.yml](../../.github/workflows/terraform.yml), [.github/workflows/deploy.yml](../../.github/workflows/deploy.yml), [.github/workflows/quality-gate.yml](../../.github/workflows/quality-gate.yml)
- Terraform: [terraform/main.tf](../../terraform/main.tf), [terraform/observability.tf](../../terraform/observability.tf)
- Runbook: [OPERATIONS.md](../OPERATIONS.md)
