# Ciclo de Vida do Software — NossoDireito v1.34.4+

**Versão:** 1.0  
**Atualizado:** 2026-05-29  
**Mantém:** Confiabilidade, LGPD compliance, integridade de dados

---

## 📋 Visão Geral

O ciclo de vida de cada **mudança** em nossodireito segue 5 fases críticas:

```
┌─────────────────────────────────────────────────────────────────────┐
│ DEV MACHINE (local)                                                  │
│  └─ Phase 1: Pre-commit gates                                       │
│      ├─ gitleaks (secrets?)                                         │
│      ├─ npm test:js (62 unit tests)                                 │
│      └─ validate_all.py (content, schema, legal)                    │
│          (Falha? código não faz commit)                             │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ GIT + GITHUB                                                         │
│  └─ Phase 2: Pre-PR checklist                                       │
│      ├─ branch naming: feat/*, fix/*, chore/*, docs/*              │
│      ├─ commit message: Conventional Commits                        │
│      └─ PR description: checklist + changes + tests                │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ GITHUB ACTIONS (CI/CD)                                              │
│  └─ Phase 3: Automated Quality Gates (13 workflows)                │
│      ├─ Security:                                                   │
│      │   ├─ CodeQL (semantic analysis)                             │
│      │   ├─ gitleaks (secrets scan)                               │
│      │   ├─ dependency-review (CVE check)                         │
│      │   └─ checkov (IaC compliance)                              │
│      │                                                              │
│      ├─ Content Quality:                                            │
│      │   ├─ validate_all.py --quick (5 validators)               │
│      │   ├─ check_doc_links.mjs (README/docs consistency)        │
│      │   ├─ check_docs_truth.mjs (frontmatter sync)              │
│      │   └─ check_version_sync.mjs (7-point version guard)       │
│      │                                                              │
│      ├─ Link Integrity:                                             │
│      │   └─ lychee (external URLs, 45m timeout)                  │
│      │      com .lycheeignore (gov.br anti-bot exemptions)       │
│      │                                                              │
│      ├─ Performance & A11y:                                         │
│      │   ├─ lighthouse (perf/SEO/a11y/best-practices)            │
│      │   └─ axe-core (WCAG 2.1 AA issues)                        │
│      │                                                              │
│      ├─ Infrastructure:                                             │
│      │   ├─ terraform plan (drift detection)                      │
│      │   └─ tflint (style + best practices)                       │
│      │                                                              │
│      └─ Supply Chain:                                               │
│          ├─ SBOM generation (packages manifest)                    │
│          ├─ Scorecard (repo security posture)                      │
│          └─ GitHub security alerts (auto-remediation)             │
│                                                                     │
│      ⛔ SE QUALQUER GATE FALHA: PR fica BLOCKED até fix            │
│      ✅ SE TODOS PASSAM: Auto-merge queued (com --delete-branch)  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ INTEGRATION (main branch)                                           │
│  └─ Phase 4: Deploy & Monitoring                                   │
│      ├─ Azure App Service auto-deploys (webhook)                   │
│      ├─ Health check: /health endpoint                             │
│      └─ Release tag: v1.34.4+n (semantic versioning)              │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PRODUCTION (nossodireito.fabiotreze.com)                           │
│  └─ Phase 5: Runtime Monitoring & Retrofeeding                    │
│      ├─ App Insights (telemetry, errors)                          │
│      ├─ Freshness check (weekly): fontes legais são atuais?       │
│      └─ Periodic audits (monthly): LGPD, security baseline        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔵 Phase 1: Pre-commit Gates (Local)

**Objetivo:** Evitar commits que quebram a build ou violam policy.

### Git Hooks (`.githooks/`)

Instalados via `npm prepare` (executed on `npm install`):

| Hook | Comando | Falha em |
|---|---|---|
| `pre-commit` | `gitleaks detect` | Secret patterns (API keys, tokens, etc.) |
| `pre-commit` | `npm run test:js` | Any test failure |
| `pre-push` | (mesmo) | Reforça a barreira antes de push |

### Local Validation

```bash
# Rodar antes de commit (desenvolvimento normal):
npm run validate           # validate_all.py --quick (5 validators, ~5sec)
npm run check:docs        # links + frontmatter consistency
npm run security:headers  # headers check on live endpoint
npm test                  # pytest (Python tests, if any)
npm run test:js          # Node tests (62 tests, ~100ms)
```

**Resultado:** Se tudo OK → segue commit. Se não → fix local ou aborta.

---

## 🟢 Phase 2: GitHub PR Gates

**Objetivo:** Garantir que o código é seguro, documentado, testado e compliant antes de merge.

### Requerimentos de PR

Antes de submeter, **verificar**:

- [ ] Branch name segue padrão (`feat/*/`, `fix/*/`, `chore/*/`, `docs/*/`)
- [ ] Commit message segue Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- [ ] Descrição do PR inclui:
  - Contexto (issue #)
  - O que muda
  - Impacto (backend? frontend? data?)
  - Screenshots (se UI)
  - Testes adicionados

### Status Checks Automáticos

Todas as 13 workflows rodam **em paralelo** (exceto `terraform` que precisa do plan):

```yaml
# Sequence:
1. CodeQL (semantic) + gitleaks (secrets) — 3min
2. Dependency review (CVE) — 1min
3. validate_all.py (content) — 2min
4. lychee (links) — 15-45min (timeout 45m)
5. lighthouse (perf) — 5min
6. axe-core (a11y) — 2min
7. terraform plan (drift) — 3min + tflint
8. SBOM + Scorecard — 2min

PARALLEL MEAN TIME: ~45min (limited by lychee timeout)
```

**Se algum falha:** Bloqueador automático. Precisa de fix + commit novo.

---

## 🟠 Phase 3: Merge & Auto-Deploy

**Condição:** Todos os gates passaram ✅

```bash
gh pr merge <PR> --auto --squash --delete-branch
```

Ações automáticas:
1. Squash merge para main (história limpa)
2. Branch deletado (`--delete-branch`)
3. Release tag gerada (semver)
4. GitHub Actions dispara deploy

---

## 🟡 Phase 4: Continuous Operations

### Deploy Automático (Azure App Service Webhook)

- App Service se registra em GitHub
- Quando código chega em `main`, webhook dispara
- Deploy leva ~3-5 min
- Health check valida `/health` endpoint

### Monitoramento em Tempo Real

```bash
# Depois do deploy:
curl https://nossodireito.fabiotreze.com/health | jq .version
# Esperado: {"version":"1.34.4", "status":"healthy", ...}
```

### Validação de Versão

Script `check_version_sync.mjs` valida 7 pontos em CI. Se houver divergência:
- `package.json` (fonte canônica)
- `data/dicionario_pcd.json` (`"versao"`)
- `docs/README.md`, `docs/ARCHITECTURE.md`, etc. (` **Versão:** `)
- `GOVERNANCE.md`, `SECURITY_AUDIT.md` (título ou cabeçalho)
- `index.html` (cache-busters `?v=`)

**Falha de sincronização?** Build fica vermelho até fix.

---

## 🔴 Phase 5: Ongoing Maintenance & Retrofeeding

### Weekly Automated Checks

#### Freshness Check (CI job, seg-sex)
- `scripts/freshness_open_issue.py` valida fontes legais
- Se governo removeu lei ou URL morreu → issue de warning
- Validação real (não HTTP-ping): `validate_legal_sources.py` parsa conteúdo

#### Security Baseline (mensal)
```bash
npm run security:headers
# Valida: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, etc.
```

### Monthly Audits

| Auditoria | Comando | Checklist |
|---|---|---|
| **LGPD Compliance** | Review [LGPD-COMPLIANCE.md](LGPD-COMPLIANCE.md) | Consentimento, retenção, direitos, DPO |
| **Azure Costs** | `assess-azure <sub-id>` | Relatório Excel + diagrama |
| **Security Posture** | GitHub > Security > Alerts | CVE, secret scanning, code scanning |
| **Dependency Updates** | Dependabot PRs | Review + approve automaticamente (Flex) |
| **Terraform Drift** | `terraform plan -refresh-only` | Detecta mudanças manuais no Portal |

### Quarterly Reviews

| Aspecto | Dono | Gate |
|---|---|---|
| **Testes** | @dev | Coverage <60%? Block release. |
| **Conteúdo** | @legal | Mudanças em direitos? Revisar com especialista. |
| **Performance** | @dev | LCP >2.5s? Investigar. |
| **LGPD** | @dpo | Dados retentos além do SLA? Notificar & remediate. |

---

## 🎯 Validadores Críticos (Que Não São Testes, Mas São Confiabilidade)

### `validate_all.py --quick` (Master Orchestrator)

Chamado em CI e localmente, executa **sequencialmente**:

```python
# validate_all.py subprocesses:
1. validate_schema.py      → Todas as .json estão conformes ao schema?
2. validate_content.py     → Encoding, encoding_utf8, missing required fields?
3. validate_legal_compliance.py → Citações legais são válidas?
4. validate_legal_sources.py    → URLs oficiais existem e estão atuais?
5. validate_sources.py     → Metadados de fonte (link, ano, etc.)?
```

**Timeout global:** 30 segundos. Se exceder → erro.

### Exemplo Real: Issue #189 (Auditoria Completa)

Descobriu:
- Version desincronizada em 7 arquivos (PR #217)
- Terraform CKV2_AZURE_32 como skip desnecessário (PR #215)
- Backend remoto não documentado (PR #213)
- LGPD checklist faltando (PR #212)

**Remediado:** Sequência de 5 PRs, 1 por 1, com testes e validação em cada.

---

## 🚀 Propostas para Automação + Increments

### 1. Renovação Automática de Dados (Semanal)

```bash
# scripts/auto-refresh-sources.mjs (novo)
# Roda toda segunda 09:00 UTC (workflow cron):
1. Faz git checkout -b chore/auto-refresh-$(date +%Y%m%d)
2. Executa validate_legal_sources.py --update
3. Se mudanças: git commit -m "chore: auto-refresh de fontes legais"
4. git push + gh pr create --auto-merge
5. Se merge OK: fecha issue de freshness anterior
```

### 2. Renovação de Dependências (Semanal)

```bash
# Dependabot já faz, mas podemos auto-merge se:
# - npm audit passed
# - license OK
# - não é breaking change
```

### 3. Renovação de Versão (Manual, mas Guiado)

```bash
# scripts/bump-version.sh <major|minor|patch>
# 1. Atualiza package.json version
# 2. Executa check_version_sync.mjs --update-all
# 3. Cria commit + PR
# 4. Testes passam? Auto-merge
```

### 4. Relatório de Saúde (Mensal)

```bash
# scripts/health-report.py (new, scheduled workflow)
# Outputs:
# - Último deploy: YYYY-MM-DD
# - Cobertura de testes: X%
# - Vulnerabilidades: 0
# - Branches estale: N
# - Errors no App Insights: 0
# → Abre issue de "Monthly Health Check" com resultados
```

---

## 📊 Confiabilidade Metrics

### Atual (v1.34.4)

| Métrica | Valor | Target | Status |
|---|---|---|---|
| Cobertura de testes (code) | 0.18% | 60% | ❌ Crítica |
| Cobertura de validação (data) | 99.5% | 99%+ | ✅ |
| Uptime (App Service SLA) | 99.95% | 99%+ | ✅ |
| Segurança (CVE) | 0 | 0 | ✅ |
| LGPD compliance | 100% | 100% | ✅ |
| Build success rate | 96% | 95%+ | ✅ |
| Deploy time | 3-5 min | <10 min | ✅ |

### Roadmap para 60%+ Cobertura de Testes

**Fase 1 (Q2 2026):** Adicionar testes para 10 funções críticas em `lib/`:
- `redis-client.js` (cache validation)
- `ai-analyze.js` (PII detection)
- `rate-limit.js` (quota enforcement)
- `security-headers.js` (baseline check)

**Fase 2 (Q3 2026):** E2E scenarios (Playwright):
- Fluxo de busca → resultado
- Consentimento IA → análise → resultado
- Revogação de consentimento

---

## 🔧 Scripts Críticos (Invocação Path)

```
User commits locally
  ↓
.git/hooks/pre-commit (gitleaks, npm test:js)
  ↓
git push
  ↓
GitHub Actions (13 workflows in parallel)
  ├─ .github/workflows/codeql.yml
  ├─ .github/workflows/gitleaks.yml
  ├─ .github/workflows/quality-gate.yml
  │   └─ scripts/validate_all.py --quick
  │       ├─ scripts/validate_content.py
  │       ├─ scripts/validate_legal_compliance.py
  │       ├─ scripts/validate_legal_sources.py
  │       └─ scripts/validate_schema.py
  ├─ .github/workflows/link-check.yml
  │   └─ lychee (c/ .lycheeignore)
  ├─ .github/workflows/accessibility.yml
  │   └─ scripts/a11y_audit.mjs (?)
  ├─ .github/workflows/lighthouse.yml
  ├─ .github/workflows/terraform.yml
  └─ .github/workflows/dependency-review.yml
  ↓
IF all ✅: auto-merge queued
  ↓
main updated + GitHub webhook fires Azure deploy
  ↓
App Service pulls + restarts
  ↓
Production health check: /health → v1.34.4
```

---

## 📋 Checklist: Antes de Cada Release

```
[ ] Todos os testes passam (npm run test:js)
[ ] Validação de conteúdo OK (npm run validate)
[ ] Version sincronizada (check_version_sync.mjs OK em CI)
[ ] No security findings (CodeQL, gitleaks = 0)
[ ] No CVE (dependency-review = approved)
[ ] Links válidos (lychee = OK)
[ ] Performance (Lighthouse = >90 em perf)
[ ] A11y OK (axe-core <3 issues, "Region" accepted)
[ ] Terraform plan = no changes
[ ] Release notes pronta (changelog.md)
[ ] Deployment SOP (rollback plan documented)
```

---

## 🎓 Conclusão

NossoDireito opera em **5 fases integradas** que garantem:

1. **Confiabilidade:** Testes + validação em cada layer
2. **Compliance:** LGPD checklist + security baseline contínuos
3. **Traceability:** Git history limpo (squash merge) + tags semver
4. **Automation:** Gates automáticos, deploy automático, renovação de dados
5. **Observability:** App Insights + health checks + retrofeeding mensal

**Próximos passos:** Aumentar cobertura de testes de 0.18% → 60% e implementar auto-refresh de dados (propostas section acima).
