# 🤖 Agents — NossoDireito

> ⚠️ **DESCONTINUADO em 2026-05-27** — Os 9 agents originais (legal-source-auditor,
> content-freshness-monitor, compliance-drift-detector, community-insights,
> dependency-intelligence, documentation-keeper, performance-watchdog,
> conecta-govbr-sync, lexml-law-drift) foram desativados como parte da
> simplificação do pipeline.
>
> - Workflows: renomeados para `.yml.disabled` em [`.github/workflows/`](../.github/workflows/) (reversível).
> - Scripts: arquivados em [`scripts/legacy/`](../scripts/legacy/) (reversível).
>
> A operação passa a depender apenas dos 8 workflows essenciais (deploy,
> quality-gate, codeql, gitleaks, lighthouse, accessibility, terraform,
> dependabot-auto-merge). Monitoramento de fontes/conteúdo agora é manual
> (quinzenal) via `python3 scripts/validate_all.py`.
>
> O documento abaixo é mantido apenas como referência histórica.

---

## Visão Geral (histórico)

Os agents são workflows GitHub Actions que rodam periodicamente para detectar problemas, sugerir melhorias e manter qualidade. Cada agent é independente e pode ser executado manualmente via `workflow_dispatch`.

---

## 📋 Agents Disponíveis

### 1. 🔗 Legal Source Auditor
**Workflow:** `.github/workflows/legal-source-auditor.yml`  
**Script:** `scripts/agent_legal_source_auditor.py`  
**Schedule:** Toda terça-feira às 08:00 UTC

**O que faz:**
- Valida URLs em `data/direitos.json`
- Detecta links quebrados
- Identifica fontes não revisadas há > 90 dias
- Detecta leis possivelmente revogadas

**Execução manual:**
```bash
gh workflow run legal-source-auditor.yml -f create_issue=true
```

---

### 2. 🔐 Compliance Drift Detector
**Workflow:** `.github/workflows/compliance-drift-detector.yml`  
**Script:** `scripts/agent_compliance_drift.py`  
**Schedule:** Toda segunda-feira às 01:00 UTC

**O que faz:**
- Executa `master_compliance.py` semanalmente
- Mantém baseline em `.github/state/compliance_baseline.json`
- Alerta se score cair > 5 pontos
- Cria issue automaticamente com drift detectado

**Execução manual:**
```bash
gh workflow run compliance-drift-detector.yml -f threshold=5
```

---

### 3. 📦 Dependency Intelligence
**Workflow:** `.github/workflows/dependency-intelligence.yml`  
**Script:** `scripts/agent_dependency_intelligence.py`  
**Schedule:** Toda quarta-feira às 02:00 UTC

**O que faz:**
- Analisa `npm outdated` + `npm audit`
- Categoriza updates: safe (patch), minor, major (breaking)
- Identifica vulnerabilidades
- Gera relatório markdown

**Execução manual:**
```bash
gh workflow run dependency-intelligence.yml
```

---

### 4. 📚 Content Freshness Monitor
**Workflow:** `.github/workflows/content-freshness-monitor.yml`  
**Script:** `scripts/agent_content_freshness_monitor.py`  
**Schedule:** 1º e 15º de cada mês às 11:00 UTC

**O que faz:**
- Detecta benefícios não revistos há > 90 dias
- Integra com `discover_benefits.py` para novos candidatos
- Cria issue consolidada com itens para revisão

**Execução manual:**
```bash
gh workflow run content-freshness-monitor.yml -f threshold_days=90
```

---

### 5. 📖 Documentation Keeper
**Workflow:** `.github/workflows/documentation-keeper.yml`  
**Script:** `scripts/agent_documentation_keeper.py`  
**Schedule:** Toda quinta-feira às 03:00 UTC + push em main

**O que faz:**
- Verifica consistência de versão entre arquivos
- Valida links internos em docs/
- Pode aplicar correções automaticamente com `--fix`

**Execução manual:**
```bash
gh workflow run documentation-keeper.yml -f auto_fix=true
```

---

### 6. ⚡ Performance Watchdog
**Workflow:** `.github/workflows/performance-watchdog.yml`  
**Script:** `scripts/agent_performance_watchdog.py`  
**Schedule:** Diário às 04:00 UTC + push em main

**O que faz:**
- Mede bundle sizes (JS/CSS)
- Mede build time
- Mantém baseline em `.github/state/performance_baseline.json`
- Alerta se houver regressão > 5%

**Execução manual:**
```bash
gh workflow run performance-watchdog.yml -f threshold=5
```

---

### 7. 👥 Community Insights
**Workflow:** `.github/workflows/community-insights.yml`  
**Script:** `scripts/agent_community_insights.py`  
**Schedule:** Toda sexta-feira às 05:00 UTC

**O que faz:**
- Analisa issues fechadas dos últimos 30 dias
- Detecta tópicos recorrentes (FAQ candidates)
- Identifica categorias com mais dúvidas
- Gera relatório markdown

**Execução manual:**
```bash
gh workflow run community-insights.yml -f days=30
```

---

## 🗂️ Estado Persistente

Alguns agents mantêm estado em `.github/state/`:

- `compliance_baseline.json` — Score atual de compliance
- `performance_baseline.json` — Métricas de performance

⚠️ **Não editar manualmente.** São atualizados pelos workflows.

---

## 🏷️ Labels Criadas Automaticamente

Cada agent usa labels específicas para suas issues:

| Agent | Labels |
|-------|--------|
| Legal Source Auditor | `agent:legal-source-auditor`, `⚖️ legal-sources` |
| Compliance Drift | `agent:compliance-drift`, `🔐 compliance` |
| Content Freshness | `agent:content-freshness`, `📚 content` |
| Performance Watchdog | `agent:performance-watchdog`, `⚡ performance` |

---

## 🔄 Schedule Resumido

| Dia | Hora UTC | Agent |
|-----|---------|-------|
| Segunda | 01:00 | Compliance Drift |
| Terça | 08:00 | Legal Source Auditor |
| Quarta | 02:00 | Dependency Intelligence |
| Quinta | 03:00 | Documentation Keeper |
| Sexta | 05:00 | Community Insights |
| Diário | 04:00 | Performance Watchdog |
| 1º e 15º | 11:00 | Content Freshness Monitor |

---

## 🚀 Execução Local

Todos os agents podem rodar localmente:

```bash
# Pré-requisitos
pip install -r requirements.txt

# Exemplo: Legal Source Auditor (sem criar issue)
python scripts/agent_legal_source_auditor.py

# Exemplo: Performance Watchdog
python scripts/agent_performance_watchdog.py
```

Sem `GITHUB_TOKEN`, agents apenas geram relatórios locais (não criam issues).

---

## 🔧 Customização

Para ajustar thresholds, editar inputs no `workflow_dispatch` de cada YAML:

```yaml
inputs:
  threshold:
    description: "Custom threshold"
    default: "5"
    type: string
```

---

## ❌ Desabilitar um Agent

Para desabilitar temporariamente, comentar o `schedule:` no YAML:

```yaml
on:
  # schedule:
  #   - cron: "0 8 * * 2"  # DESABILITADO
  workflow_dispatch:
```

---

**Última atualização:** 2026-05-23
