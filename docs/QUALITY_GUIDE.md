# Guia de Qualidade — NossoDireito

> **Status:** 🟢 Ativo
> **Versão:** 1.16.0 | **Atualizado:** 2026-05-17
> **Escopo:** Quick-start, pipeline de qualidade, scripts, testes e troubleshooting
> **Consolida:** QUALITY_SYSTEM + QUALITY_TESTING_GUIDE + GUIA_RAPIDO_USO + OPCOES_EXECUCAO + TESTING + VALIDATION_STATUS

## Sumário

- [0. Quick Start — Do Zero aos Testes](#0-quick-start--do-zero-aos-testes)
- [1. Visão Geral do Pipeline](#1-visão-geral-do-pipeline)
- [2. Referência de Scripts](#2-referência-de-scripts)
- [3. Guia de Execução](#3-guia-de-execução)
- [4. Testes Manuais de Browser](#4-testes-manuais-de-browser)
- [5. Troubleshooting](#5-troubleshooting)
- [6. Métricas e Interpretação](#6-métricas-e-interpretação)

---

## 0. Quick Start — Do Zero aos Testes

### Pré-requisitos

| Ferramenta | Versão mínima | Verificar |
|---|---|---|
| Python | 3.10+ | `python --version` |
| Node.js | 22+ | `node --version` |
| Git | qualquer | `git --version` |

### Copiar e colar (tudo de uma vez)

```bash
git clone https://github.com/fabiotreze/nossodireito.git
cd nossodireito
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt -r requirements-dev.txt
playwright install chromium
pytest tests/ -v                         # Testes unitários (~709)
pytest tests/test_e2e_playwright.py -v   # Testes E2E (~137)
python scripts/validate_content.py       # Validação de conteúdo
python scripts/master_compliance.py      # Auditoria completa (100%)
node server.js                           # Servidor local → http://localhost:8080
```

### Problemas comuns

| Problema | Solução |
|---|---|
| `ModuleNotFoundError: No module named 'pytest'` | `pip install -r requirements-dev.txt` |
| `playwright install` falha | Verifique conexão com internet |
| Testes E2E: "porta em uso" | Feche servidores na porta 9876 |
| `python` não encontrado | Use `python3` (Mac/Linux) |
| `UnicodeDecodeError` (Windows) | `$env:PYTHONIOENCODING='utf-8'; python script.py` |

---

## 1. Visão Geral do Pipeline

### Hierarquia (2 entry points, 7 leaf validators)

```
┌─────────────────────────────────────────────────────────────┐
│  ENTRY POINTS (chame APENAS estes — nunca os leaves direto) │
├─────────────────────────────────────────────────────────────┤
│  master_compliance.py  → Pre-commit + CI quality-gate       │
│                          21 categorias, ~1080 pts, ~30s     │
│                          Invoca: analise360                 │
│                                                              │
│  validate_all.py       → CI/CD deploy + weekly-review       │
│                          16 fases, inclui HTTP, ~3-5min     │
│                          Invoca: validate_schema,           │
│                                  validate_content,          │
│                                  validate_sources,          │
│                                  validate_urls,             │
│                                  validate_legal_sources,    │
│                                  validate_legal_compliance, │
│                                  audit_automation,          │
│                                  complete_beneficios        │
└─────────────────────────────────────────────────────────────┘
       │
       └─── LEAF VALIDATORS (não chamar manualmente) ──────────
            • validate_schema.py        — JSON Schema Draft 7
            • validate_content.py       — 85+ checks semânticos
            • validate_sources.py       — URLs .gov.br vivas
            • validate_urls.py          — 318 URLs c/ whitelist
            • validate_legal_sources.py — leis, artigos, CIDs
            • validate_legal_compliance.py — disclaimer, LGPD
            • audit_automation.py       — mapeamento auto
            • complete_beneficios.py    — preencher campos
            • analise360.py             — 807 checks cobertura

       └─── UTILS (chamada manual sob demanda) ────────────────
            • bump_version.py           — release tooling
            • discover_benefits.py      — cron mensal (novos PcDs)
```

### Ordem de execução por gatilho

| Gatilho | Comando único | Duração |
|---|---|---|
| **Local: `git commit`** | `master_compliance.py --quick` (via `scripts/pre-commit`) | ~30s |
| **CI: quality-gate.yml** | `validate_all.py --quick` | ~60s |
| **CI: deploy.yml** | `pytest tests/` → `validate_all.py --quick` | ~3min |
| **CI: weekly-review.yml** | `validate_all.py --quick` → `validate_sources.py --urls` → `discover_benefits.py` | ~10min |
| **CI: discover-benefits.yml** (cron 1º do mês) | `discover_benefits.py --since 60` | ~5min |

> Regra de ouro: **se você está pensando em rodar um validator leaf manualmente, está fazendo errado.** Use um dos 2 entry points.

### Pre-commit Hook — Comando Único

O hook `scripts/pre-commit` executa **um único comando**:

```
master_compliance.py --quick
  ├── STEP 0: Versão (fail-fast — aborta se inconsistente em 10 arquivos)
  ├── STEP 1: JSON Schema Draft 7 (direitos.json)
  ├── STEP 2: 21 categorias de scoring (~1080 pts, sem HTTP)
  └── STEP 3: analise360.py via subprocess (35 pts adicionais)
```

| O que faz | Fail-fast? | Duração |
|---|---|---|
| Versão: 10 arquivos vs `package.json` | **SIM** | 0.1s |
| Schema: `direitos.json` vs JSON Schema Draft 7 | NÃO | 0.5s |
| 21 categorias: dados, código, segurança, etc. | NÃO | ~25s |
| analise360.py (cobertura, IPVA, completude) | NÃO | ~5s |

**Instalação:** `cp scripts/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`

**Bypass (emergência):** `git commit --no-verify`

### O que NÃO roda no pre-commit

| Excluído | Motivo |
|---|---|
| `pytest tests/` (9 testes) | Coberto por master_compliance (usar no CI) |
| `test_e2e_playwright.py` (42 testes) | Requer `node server.js` + Chromium |
| `validate_all.py` (16 fases) | Inclui HTTP (~3min — usar no CI/manual) |
| `validate_sources.py --urls` | HTTP live (~60-180s) |
| `discover_benefits.py` | Cron mensal (workflow dedicado) |

---

## 2. Referência de Scripts

### 2.1 Entry points (use estes)

#### `master_compliance.py` — Motor de Qualidade (pre-commit + quality-gate CI)

```bash
python scripts/master_compliance.py --quick  # ~30s (sem HTTP)
python scripts/master_compliance.py          # ~1-5min (com HTTP)
```

**21 categorias scoradas:** Dados, Código, Fontes, Arquitetura, Documentação, Segurança, Performance, Acessibilidade, SEO, Infraestrutura, Testes E2E, Dead Code, Órfãos, Lógica, Regulatory, Cloud Security, CI/CD, Dependências, Changelog, Análise 360° (via subprocess `analise360.py`), Referências Órfãs.

#### `validate_all.py` — Orquestrador estendido (CI deploy + weekly)

```bash
python scripts/validate_all.py           # 16 fases completas, com HTTP
python scripts/validate_all.py --quick   # Fases 1-4 (sem HTTP)
python scripts/validate_all.py --fix     # Validar + auto-corrigir
```

**Output:** `validation_report.json`. Invoca todos os leaf validators abaixo via subprocess.

### 2.2 Leaf validators (chamados pelos entry points — não rodar diretamente)

| Script | Quem chama | Responsabilidade |
|---|---|---|
| `validate_schema.py` | `validate_all` Fase 1 | JSON Schema Draft 7 |
| `validate_content.py` | `validate_all` Fase 2 | 85+ checks semânticos (categorias, IPVA, matching) |
| `validate_sources.py` | `validate_all` Fase 5, `deploy.yml`, `weekly-review.yml` | URLs .gov.br vivas (HTTP) |
| `validate_urls.py` | `validate_all` Fase 7, `weekly-review.yml` | 318 URLs c/ whitelist internacional |
| `validate_legal_sources.py` | `master_compliance` (subprocess) | Leis, artigos, CIDs |
| `validate_legal_compliance.py` | `validate_all` (extras) | Disclaimer, LGPD, isenção |
| `audit_automation.py` | `validate_all` Fase 12 | Mapeamento de automação |
| `complete_beneficios.py` | `validate_all` Fase 13 | Templates p/ campos parciais |
| `analise360.py` | `master_compliance` (subprocess) | 807 checks de cobertura, IPVA 27 UFs |

### 2.3 Utils (chamada manual ou por workflow dedicado)

| Script | Quando rodar |
|---|---|
| `bump_version.py <versão>` | Antes de release (atualiza 10 arquivos) |
| `discover_benefits.py --since N` | Cron mensal (`discover-benefits.yml`) — descobre novos PcDs no DOU/Senado |

---

## 3. Guia de Execução

### 3.1 Pre-Commit Hook (automatizado)

```bash
cp scripts/pre-commit .git/hooks/pre-commit
```

Executa `master_compliance.py --quick` automaticamente: versão (fail-fast) → schema → 21 categorias.
Se falhar, commit é **bloqueado**. Bypass: `git commit --no-verify -m "msg"` (não recomendado).

### 3.2 GitHub Actions CI/CD

Workflow `.github/workflows/quality-gate.yml`:
- **Triggers:** Push main/develop, PRs para main
- **Steps:** Checkout → Python 3.11 → Limpeza → Sintaxe → Conteúdo → Quality Gate → Segurança → Performance → Relatório (artifact 30 dias)

### 3.3 Workflows Recomendados

**Diário (pré-commit — automático via hook):**

```bash
python scripts/master_compliance.py --quick
# Deve retornar 100%
```

**Semanal:**

```bash
python scripts/validate_all.py --fix
python scripts/analise360.py
python scripts/validate_sources.py
python scripts/validate_urls.py
# Backup manual:
cp data/direitos.json "backups/direitos_$(date +%Y%m%d).json"
```

**Antes de release:**

```bash
python scripts/analise360.py
```

**Mensal:**

```bash
python scripts/audit_automation.py
# Revisar documentação, atualizar CHANGELOG.md
# Validar acessibilidade online (AccessMonitor, WAVE, AccessibilityChecker)
```

### 3.4 PowerShell Shortcuts

```powershell
# Adicionar ao $PROFILE:
function Validate-NossoDireito { $env:PYTHONIOENCODING='utf-8'; python scripts/master_compliance.py @args }
Set-Alias nv Validate-NossoDireito

function Validate-Quick { $env:PYTHONIOENCODING='utf-8'; python scripts/master_compliance.py --quick }
Set-Alias nvq Validate-Quick

function Validate-All { $env:PYTHONIOENCODING='utf-8'; python scripts/validate_all.py @args }
Set-Alias nva Validate-All

function Analise360 { $env:PYTHONIOENCODING='utf-8'; python scripts/analise360.py }
Set-Alias n360 Analise360
```

---

## 4. Testes Manuais de Browser

### 4.1 Carregamento Inicial

- [ ] Página carrega em <3s, nenhum erro no Console
- [ ] 30 categorias visíveis, logo "NossoDireito" presente
- [ ] Disclaimer visível no rodapé, VLibras widget no canto inferior direito

### 4.2 Busca e Matching Engine

- [ ] "autismo" → CIPTEA, educação, plano_saude
- [ ] "BPC" → BPC, "carro" → isencoes_tributarias
- [ ] "trabalho" → trabalho, cotas
- [ ] Termo inexistente → "Nenhuma categoria encontrada"
- [ ] Limpar busca → restaura todas, case-insensitive

### 4.3 Categorias (30)

Para CADA categoria verificar:
1. Modal abre suavemente
2. Campos completos: titulo, icone, resumo, base_legal (lei+artigo+link), requisitos, documentos, passo_a_passo, dicas, valor, onde, links
3. Links abrem em nova aba
4. Scroll completo funciona
5. Fechar: X, Esc, ou clique fora

### 4.4 IPVA Dropdown (CRÍTICO)

- [ ] "Isenções Tributárias" → dropdown com 27 estados
- [ ] AC: Lei LC 114/2002, Art. 7º, SEFAZ verificado
- [ ] SP: Lei 13.296/2008, Art. 13-A, SEFAZ verificado
- [ ] Trocar estado → informações atualizam
- [ ] Fechar/reabrir modal → dropdown resetado

```javascript
// Verificação JS Console:
direitos_data.categorias.find(c => c.id === 'isencoes_tributarias').ipva_estados.length
// Deve retornar: 27
```

### 4.5 Acessibilidade + Teclado

- [ ] Tab navega entre categorias, Enter abre modal, Esc fecha
- [ ] Tab dentro do modal navega links, Shift+Tab volta
- [ ] Estilos de foco visíveis (outline azul/preto)
- [ ] VLibras carrega e funciona (desktop)

### 4.6 Responsividade

| Dispositivo | Colunas | Modal Width |
|-------------|---------|-------------|
| Desktop (>1024px) | 3-4 | ~70% |
| Tablet (768-1024px) | 2-3 | ~80% |
| Mobile (<768px) | 1 | 95%, textos ≥16px, botões ≥44px |

### 4.7 Performance (Lighthouse)

| Métrica | Meta | Esperado |
|---------|------|----------|
| Performance | ≥90 | 95+ |
| Accessibility | ≥95 | 98+ |
| Best Practices | ≥90 | 100 |
| SEO | ≥90 | 95+ |

### 4.8 Pre-Deploy Checklist

- [ ] `python scripts/validate_all.py` → 100%
- [ ] Todas 30 categorias testadas manualmente
- [ ] IPVA 10+ estados verificados
- [ ] VLibras funcional, Lighthouse ≥90
- [ ] CHANGELOG.md atualizado, versão bumped
- [ ] Git tag de versão

---

## 5. Troubleshooting

### Encoding (Windows)

```bash
# UnicodeDecodeError com emojis:
$env:PYTHONIOENCODING='utf-8'; python script.py
```

### Módulos Faltando

```bash
pip install -r requirements.txt
```

### Commit Bloqueado

```bash
git commit --no-verify -m "msg"  # bypass temporário
```

### JSON Inválido

```bash
python -m json.tool data/direitos.json > $null  # testa sintaxe
```

### Pipeline Timeout (validate_sources.py)

```bash
python scripts/validate_all.py --quick  # pula validação de URLs
```

### Quality Gate Falhou (score <75)

1. Executar `python scripts/validate_all.py` e ler relatório
2. Identificar categoria com score baixo
3. Corrigir e re-executar

### IPVA Dropdown Não Funciona

1. F12 (DevTools) → Console → ver erros JS
2. Verificar: `direitos_data.categorias.find(c => c.id === 'isencoes_tributarias').ipva_estados.length` → 27
3. Ctrl+Shift+R (hard reload)

### VLibras Não Carrega

1. Verificar scripts no HTML: `vlibras-plugin.js` + `new window.VLibras.Widget(...)`
2. Verificar CSP exceptions para `*.vlibras.gov.br`
3. Ver seção VLibras em [KNOWN_ISSUES.md](KNOWN_ISSUES.md)

### Base Legal Incompleta

```json
// ❌ Falta artigo:
{ "lei": "Portaria MEC nº 389/2013", "url": "https://sisu.mec.gov.br" }

// ✅ Correto:
{ "lei": "Portaria MEC nº 389/2013", "artigo": "Art. 1º", "url": "https://sisu.mec.gov.br" }
```

---

## 6. Métricas e Interpretação

### Master Compliance

| Score | Status |
|-------|--------|
| 100% | 🏆 PERFEITO |
| 99-99.9% | ✅ EXCELENTE |
| 95-98.9% | ⚠️ BOM |
| 90-94.9% | ⚠️ ATENÇÃO |
| <90% | ❌ CRÍTICO |

### validate_all.py

| Score | Status |
|-------|--------|
| 100% | 🏆 PERFEITO |
| ≥80% | ✅ EXCELENTE |
| 60-79% | ⚠️ BOM |
| <60% | ❌ CRÍTICO |

### Análise 360°

| Métrica | OK | BOM | Implementar mais |
|---------|-----|-----|-----------------|
| Cobertura | ≥75% | 60-74% | <60% |
| Completude | ≥20 | 15-19 | <15 |
| IPVA | 27 | 20-26 | <20 |

### Padrões JSON

```json
{
  "id": "nova_categoria",
  "titulo": "Nova Categoria",
  "icone": "🎯",
  "resumo": "Descrição com mais de 30 caracteres",
  "base_legal": [
    { "lei": "Lei 12.345/2020", "artigo": "Art. 5º", "url": "https://planalto.gov.br/..." }
  ],
  "links": [
    { "titulo": "Site Oficial", "url": "https://exemplo.gov.br" }
  ]
}
```

### Boas Práticas

**✅ Fazer:**
1. Executar `master_compliance.py --quick` antes de cada commit (automático via pre-commit hook)
2. Backup antes de modificar direitos.json
3. Revisar conteúdo de `complete_beneficios.py` (templates genéricos)
4. Monitorar cobertura semanalmente

**❌ Não fazer:**
1. Commitar se score < 95%
2. Editar benefícios sem critérios (usar analise360.py como guia)
3. Ignorar timeouts em validate_sources.py
4. Executar --fix em produção sem backup

---

## Histórico de Alterações

| Data | Mudança |
|------|---------|
| 2026-02-15 | v1.11.0: Adicionados scripts analise360.py (807 checks), validate_urls.py (318 URLs). Tabela "Quando Usar" expandida. Workflow "Antes de release" adicionado. Scripts capture_screenshots.py, test_visual_browser.py e test_high_contrast.py arquivados em _archive/dead_code/. |
| 2026-02-13 | Criado por consolidação de QUALITY_SYSTEM + QUALITY_TESTING_GUIDE + GUIA_RAPIDO_USO + OPCOES_EXECUCAO |
| 2026-02-13 | Pipeline simplificado: 4→3 estágios, removida duplicação versão/test_complete, docs atualizados |
| 2026-02-13 | Pipeline mínimo: 3→2 estágios, removidos pytest (redundante c/ master_compliance) e fase 5 do quick (redundante c/ validate_analise_360) |
| 2026-02-13 | Pipeline comando único: pre-commit chama apenas `master_compliance.py --quick`. Absorvidos: check_version_consistency.py (inline), validate_schema.py (método), validate_all.py removido do hook. Zero duplicação, zero intermediários. |
