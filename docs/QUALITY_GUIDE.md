# Guia de Qualidade — NossoDireito

> **Status:** 🟢 Ativo
> **Versão:** 1.13.1 | **Atualizado:** 2026-02-16
> **Escopo:** Pipeline de qualidade, execução de scripts, testes manuais e troubleshooting
> **Consolida:** QUALITY_SYSTEM + QUALITY_TESTING_GUIDE + GUIA_RAPIDO_USO + OPCOES_EXECUCAO

## Sumário

- [1. Visão Geral do Pipeline](#1-visão-geral-do-pipeline)
- [2. Referência de Scripts](#2-referência-de-scripts)
- [3. Guia de Execução](#3-guia-de-execução)
- [4. Testes Manuais de Browser](#4-testes-manuais-de-browser)
- [5. Troubleshooting](#5-troubleshooting)
- [6. Métricas e Interpretação](#6-métricas-e-interpretação)

---

## 1. Visão Geral do Pipeline

### Arquitetura de Validação (2 componentes)

| Componente | Script | Papel |
|-----------|--------|-------|
| **Gatilho** | `pre-commit` (hook Git) | Comando único, bloqueia commit se falhar |
| **Motor de qualidade** | `master_compliance.py --quick` | 21 categorias, ~1050 pts, fail-fast versão, JSON Schema |

> `validate_all.py` permanece para rodadas **manuais completas** (16 fases, inclui HTTP).

### O que Validamos

- ✅ 30 categorias completas (todos os campos obrigatórios)
- ✅ 27 estados no dropdown IPVA (lei, artigo, SEFAZ)
- ✅ Matching engine (keywords, sinônimos, termos uppercase)
- ✅ Fontes oficiais (gov.br, planalto.gov.br)
- ✅ 88 relacionamentos entre categorias e documentos
- ✅ Padrões de código (sem alert(), error handling, ARIA)
- ✅ Análise semântica (resumos, dicas, valores monetários)
- ✅ Segurança (HTTPS, CSP, dados sensíveis)
- ✅ Performance (HTML <100KB, JS <100KB, CSS <100KB)
- ✅ JS syntax check (`node -c`)
- ✅ Workspace hygiene (temp files, orphans, duplicates)
- ✅ JSON Schema Draft 7 (direitos.json vs schema)
- ✅ Consistência de versão (10 arquivos vs package.json)

### Pre-commit Hook — Comando Único

O hook `scripts/pre-commit` executa **um único comando** a cada `git commit`:

```
master_compliance.py --quick
  ├── STEP 0: Versão (fail-fast — aborta se inconsistente)
  ├── STEP 1: JSON Schema Draft 7
  └── STEP 2: 21 categorias (sem HTTP, ~30s)
```

| O que faz | Fail-fast? | Duração |
|-----------|------------|--------|
| Versão: 10 arquivos vs `package.json` | **SIM** (aborta imediatamente) | 0.1s |
| Schema: `direitos.json` vs JSON Schema Draft 7 | NÃO | 0.5s |
| 21 categorias: dados, código, arquitetura, segurança, etc. | NÃO | ~30s |

> **Por que comando único?** Tudo absorvido internamente no `master_compliance.py`:
> versão, schema, análise 360°, e todos os checks de dados.
> Zero duplicação, zero arquivos intermediários.

**Instalação:**
```bash
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Bypass (emergência):** `git commit --no-verify`

### Testes que não rodam no pre-commit

| Teste | Checks | Motivo |
|-------|--------|--------|
| `test_e2e_interactive.py` | 42 testes Playwright | Requer `node server.js` + Chromium |

| `pytest tests/` | 9 testes unitários | Coberto por master_compliance (usar no CI/CD) |
| `validate_all.py` | 16 fases completas | Inclui HTTP (usar manualmente/semanal) |

**Modos de execução:**

```bash
python scripts/master_compliance.py --quick  # ~30s (pre-commit)
python scripts/master_compliance.py          # ~1-5min (completo, com HTTP)
python scripts/validate_all.py               # ~3-5min (16 fases, com HTTP)
python scripts/validate_all.py --fix     # validar + corrigir
```

---

## 2. Referência de Scripts

### 2.1 `master_compliance.py` — Motor de Qualidade (ponto de entrada único)

```bash
python scripts/master_compliance.py --quick  # Pre-commit (~30s, sem HTTP)
python scripts/master_compliance.py          # Completo (~1-5min, com HTTP)
```

Inclui internamente: fail-fast de versão, JSON Schema Draft 7, 21 categorias de scoring.

**21 categorias:** Dados, Código, Fontes, Arquitetura, Documentação, Segurança, Performance, Acessibilidade, SEO, Infraestrutura, Testes E2E, Dead Code, Órfãos, Lógica, Regulatory, Cloud Security, CI/CD, Dependências, Changelog, Análise 360°, Referências Órfãs.

### 2.2 `validate_all.py` — Orquestrador manual (16 fases)

```bash
python scripts/validate_all.py           # Modo completo (16 fases, inclui HTTP)
python scripts/validate_all.py --quick   # Modo rápido (fases 1-4)
python scripts/validate_all.py --fix     # Validar + corrigir
```

**Output:** `validation_report.json` (exit code 0=OK, 1=falhas)

> Não faz parte do pre-commit. Usar para validações completas manuais/semanais.

### 2.3 `analise360.py` — Cobertura de Benefícios

```bash
python scripts/analise360.py
```

Valida cobertura (≥75%), completude (≥20 benefícios), IPVA (27 estados).

### 2.4 `validate_content.py` — Validador Semântico

```bash
python scripts/validate_content.py
```

Valida 85+ checks: categorias (20 campos), IPVA dropdown (27 UFs), matching engine, documentos mestre (16), relacionamentos (88), padrões de código, conteúdo semântico.

### 2.5 `validate_sources.py` — URLs .gov.br

```bash
python scripts/validate_sources.py   # ~60-180s (HTTP real)
```

### 2.6 `complete_beneficios.py` — Preenchimento de Campos

```bash
python scripts/complete_beneficios.py
```

Preenche campos faltantes com templates (mín: 5 requisitos, 4 documentos, 6 passos, 4 dicas, 2 links). ⚠️ Revise o conteúdo gerado.

### 2.7 `audit_automation.py` — Mapeamento de Automação

```bash
python scripts/audit_automation.py
```

### 2.8 `analise360.py` — Avaliação Completa (807 checks)

```bash
python scripts/analise360.py
```

807 verificações em 11 seções: SEO, segurança, acessibilidade, conteúdo, performance, legal, URLs (318). Gera relatório detalhado com percentual por seção.

### 2.9 `validate_urls.py` — Validação de URLs

```bash
python scripts/validate_urls.py
```

Valida 318 URLs do projeto (gov.br, legislação, internacionais). Whitelist `DOMINIOS_INTERNACIONAIS` para domínios como icd.who.int.

### Quando Usar Cada Script

| Situação | Script | Quando |
|----------|--------|--------|
| Antes de commit | `pre-commit` hook (automático) | A cada `git commit` |
| Bump de versão | `bump_version.py <versao>` | Antes de release |
| Verificar versão | `master_compliance.py --quick` | Automático (pre-commit) |
| Verificação completa | `validate_all.py` | Semanal |
| Avaliação 360° | `analise360.py` | Antes de release |
| Após editar benefícios | `analise360.py` | Conforme necessário |
| Completar parciais | `complete_beneficios.py` | Quando completude < 20 |
| Validar links gov.br | `validate_sources.py` | Semanal |
| Validar todas URLs | `validate_urls.py` | Antes de release |
| Planejar melhorias | `audit_automation.py` | Mensal |

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
