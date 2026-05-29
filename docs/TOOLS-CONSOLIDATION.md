# Ferramentas — Audit & Consolidação

**Versão:** 1.0  
**Atualizado:** 2026-05-29

---

## 📋 Stack Final — O Que Realmente Usamos

### ✅ Ferramentas Essenciais (Mantém)

| Ferramenta | Função | Instalação | Status |
|---|---|---|---|
| **Node.js 22 LTS** | Runtime | ~/.nvm | ✅ Active |
| **npm** | Package manager | Node.js | ✅ Active |
| **Python 3.12** | Scripts, testes | uv (formal) | ✅ Active |
| **Terraform 1.15.5** | IaC Azure | brew | ✅ Active (upgraded) |
| **GitHub CLI (gh)** | PR, deploy, issues | brew | ✅ Active |
| **Azure CLI (az)** | Cloud ops | brew | ✅ Active |
| **Docker Desktop** | Local E2E | brew | ✅ Active |
| **Git** | VCS | Xcode/brew | ✅ Active |
| **Playwright** | A11y + E2E testing | npm deps | ✅ Active |
| **Checkov** | IaC scanning | CI workflow | ✅ Active |
| **CodeQL** | SAST | CI workflow | ✅ Active |
| **Lychee** | Link checking | CI workflow | ✅ Active |
| **Lighthouse** | Perf/A11y/SEO | CI workflow | ✅ Active |
| **SBOM/Scorecard** | Supply chain | CI workflow | ✅ Active |
| **gitleaks** | Secrets scan | CI workflow | ✅ Active |
| **uv** | Python package manager | curl official | ✅ Active |

---

## 🟠 Ferramentas com Sobreposição (Consolidar)

### App Insights — Mantém (ja instalado)

| Ferramenta | Propósito | Nossodireito? | Ação |
|---|---|---|---|
| **Application Insights** | Telemetry + monitoring | ✅ YES | **MANTER** |
| **Azure Monitor** | Metrics + logs | ✅ YES | **MANTER** |
| **Sentry** | Error tracking deeper | ❌ NO | **DESCARTE** |
| **Datadog** | APM + custom metrics | ❌ NO | **DESCARTE** |
| **New Relic** | Full-stack monitoring | ❌ NO | **DESCARTE** |

**Decisão:** App Insights é suficiente para nossodireito (telemetry simples, sem need de custom dashboards complexos). Não instalar Sentry/Datadog/New Relic (redundância).

---

### Load Testing — Não Necessário

| Ferramenta | Propósito | Nossodireito? | Ação |
|---|---|---|---|
| **k6** | Load testing | ❌ NO | **DESCARTE** |
| **Apache JMeter** | Performance testing | ❌ NO | **DESCARTE** |
| **Locust** | Load simulation | ❌ NO | **DESCARTE** |

**Razão:** Nossodireito roda em B1 App Service (SKU pequeno) com ~10-100 concurrent users esperados. Load testing não é priority. Se necessário no futuro: usar k6 em PR dedicada.

---

### Performance Observability — Consolidado

| Ferramenta | Propósito | Nossodireito? | Ação |
|---|---|---|---|
| **Lighthouse CI** | Perf in CI | ✅ YES (via workflow) | **MANTER** |
| **WebPageTest** | Detailed perf analysis | ❌ NO (Lighthouse suffices) | **DESCARTE** |
| **Dynatrace** | Advanced APM | ❌ NO | **DESCARTE** |
| **Grafana** | Custom metrics dashboards | ❌ NO (App Insights OK) | **DESCARTE** |

**Decisão:** Lighthouse em CI (5 min, suficiente). App Insights para runtime metrics. Não need de WebPageTest/Dynatrace/Grafana (over-engineering).

---

### Security & Compliance — Consolidado

| Ferramenta | Propósito | Nossodireito? | Ação |
|---|---|---|---|
| **CodeQL** | Semantic code analysis | ✅ YES (CI) | **MANTER** |
| **gitleaks** | Secrets scan | ✅ YES (CI + pre-commit) | **MANTER** |
| **Checkov** | IaC compliance | ✅ YES (CI) | **MANTER** |
| **Dependabot** | Dependency scanning | ✅ YES (auto-merge) | **MANTER** |
| **OWASP ZAP** | Web app pen testing | ❌ NO (CodeQL + gitleaks suffice) | **DESCARTE** |
| **Snyk** | Vulnerability scanning | ❌ NO (redundant w/ Dependabot) | **DESCARTE** |
| **Sonarqube** | Code quality deep-dive | ❌ NO (CodeQL sufficient) | **DESCARTE** |

**Decisão:** CodeQL + gitleaks + Checkov + Dependabot formam uma cobertura suficiente. Não instalar OWASP ZAP/Snyk/Sonarqube.

---

### Data & Analytics — Não Necessário

| Ferramenta | Propósito | Nossodireito? | Ação |
|---|---|---|---|
| **Google Analytics** | Web analytics | ❌ NO (LGPD privacy-first) | **DESCARTE** |
| **Mixpanel** | User behavior tracking | ❌ NO | **DESCARTE** |
| **Segment** | Data pipeline | ❌ NO | **DESCARTE** |
| **Amplitude** | Product analytics | ❌ NO | **DESCARTE** |

**Razão:** Nossodireito é LGPD-compliant, zero tracking de usuários. App Insights telemetria é suficiente para infra health (não behavior tracking).

---

## 🟢 Stack Final Consolidado

### Ferramentas por Categoria

```
┌─────────────────────────────────────────────────────────────┐
│ DESENVOLVIMENTO LOCAL                                       │
├─────────────────────────────────────────────────────────────┤
│ • Node.js 22 LTS (runtime)                                  │
│ • Python 3.12 (scripts)                                     │
│ • Terraform 1.15.5 (IaC)                                    │
│ • Docker Desktop (local E2E)                                │
│ • Git + GitHub CLI (vcs + ops)                              │
│ • Azure CLI (cloud ops)                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TESTING                                                     │
├─────────────────────────────────────────────────────────────┤
│ • npm test (62 unit tests)                                  │
│ • Playwright (A11y + E2E, opcional)                         │
│ • pytest (Python tests, minimal)                            │
│ • Lighthouse CI (perf/a11y/seo)                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ CI/CD PIPELINE (GitHub Actions)                             │
├─────────────────────────────────────────────────────────────┤
│ • CodeQL (code scanning)                                    │
│ • gitleaks (secrets)                                        │
│ • Dependabot (dependencies + auto-merge)                    │
│ • Checkov (IaC)                                             │
│ • Lychee (link checking, 45m timeout)                       │
│ • Lighthouse (perf)                                         │
│ • SBOM + Scorecard (supply chain)                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PRODUCTION MONITORING                                       │
├─────────────────────────────────────────────────────────────┤
│ • App Insights (telemetry, errors, perf)                    │
│ • Azure Monitor (infra metrics)                             │
│ • /health endpoint (runtime checks)                         │
│ • App Service webhooks (auto-deploy)                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ INFRAESTRUTURA                                              │
├─────────────────────────────────────────────────────────────┤
│ • Terraform (IaC)                                           │
│ • Azure (App Service, Key Vault, Redis, OpenAI)            │
│ • GitHub (VCS + CI/CD)                                      │
│ • Cloudflare (edge, WAF)                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Checklist de Remocão (Não Instalar)

- [ ] ❌ Sentry (errotracking — usar App Insights)
- [ ] ❌ Datadog (monitoring — usar App Insights + Azure Monitor)
- [ ] ❌ New Relic (APM — use App Insights)
- [ ] ❌ k6 (load testing — não escopo)
- [ ] ❌ Apache JMeter (performance testing — não escopo)
- [ ] ❌ Locust (load sim — não escopo)
- [ ] ❌ WebPageTest (perf — Lighthouse suffices)
- [ ] ❌ Dynatrace (advanced APM — over-engineering)
- [ ] ❌ Grafana (custom dashboards — não need)
- [ ] ❌ OWASP ZAP (pen testing — CodeQL + gitleaks)
- [ ] ❌ Snyk (vuln scanning — redundant w/ Dependabot)
- [ ] ❌ Sonarqube (code quality — CodeQL sufficient)
- [ ] ❌ Google Analytics (tracking — LGPD private)
- [ ] ❌ Mixpanel (behavior analytics — LGPD private)
- [ ] ❌ Segment (data pipeline — não need)
- [ ] ❌ Amplitude (product analytics — LGPD private)

---

## 🎯 Conclusão

**Stack de nossodireito é lean, focused, e sem redundância:**

- ✅ 16 ferramentas essenciais instaladas
- ✅ 13 workflows CI/CD robustos
- ✅ Monitoring suficiente (App Insights + Azure Monitor)
- ✅ Testing adequado (unit + E2E + validation)
- ✅ Security forte (4 scanners em CI)
- ✅ Zero sobreposição custosa

**Não instalar:** Ferramentas que duplicam funcionalidade ou estão fora do escopo. Se necessário no futuro, revisar e decidir em PR dedicada com justificativa.

---

## 🔗 Documentação Relacionada

- [SOFTWARE-LIFECYCLE.md](SOFTWARE-LIFECYCLE.md) — Ciclo de vida
- [HEALTH-DASHBOARD.md](HEALTH-DASHBOARD.md) — Ratings & metrics
- `.github/workflows/` — Todos os 13 workflows
- `package.json` — npm deps (95 packages)
- `requirements.txt` — Python deps (18 packages)
