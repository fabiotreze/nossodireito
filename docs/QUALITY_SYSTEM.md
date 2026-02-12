# 🔍 Sistema de Qualidade NossoDireito v1.8.0

Infraestrutura completa de validação automática para garantir qualidade, segurança e conformidade antes de cada commit e deploy.

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Ferramentas de Validação](#ferramentas-de-validação)
3. [Pipeline de Qualidade](#pipeline-de-qualidade)
4. [Pre-Commit Hook](#pre-commit-hook)
5. [GitHub Actions CI/CD](#github-actions-cicd)
6. [Ordem de Execução](#ordem-de-execução)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

### O que validamos

- ✅ **25 categorias** completas com todos os campos obrigatórios
- ✅ **27 estados** no dropdown IPVA (lei, artigo, SEFAZ)
- ✅ **Matching engine** (keywords, sinônimos, termos uppercase)
- ✅ **Fontes oficiais** (gov.br, planalto.gov.br)
- ✅ **Relacionamentos** entre categorias e documentos (88 relações)
- ✅ **Padrões de código** (sem alert(), error handling, ARIA)
- ✅ **Análise semântica** (resumos, dicas, valores monetários)
- ✅ **Quality Gate** (100.0/100, WAF 100%)
- ✅ **Segurança** (HTTPS, CSP, dados sensíveis)
- ✅ **Performance** (HTML <50KB, JS <100KB, JSON <150KB)

### Score Atual

```
Quality Gate: 100.0/100
WAF 5 Pillars: 100% ✅
- Security: 100%
- Reliability: 100%
- Performance: 100%
- Cost Optimization: 100%
- Operational Excellence: 100%

Acessibilidade: 50 ARIA attributes, VLibras, keyboard navigation
Segurança: 100% HTTPS, 0 dados sensíveis
Performance: HTML 29KB, JS 71KB, JSON 102KB
```

---

## 🛠️ Ferramentas de Validação

### 1. `scripts/validate_content.py` ⭐ NOVO

**Validador semântico e estrutural completo**

```bash
python3 scripts/validate_content.py
```

**O que valida:**

#### 📦 Categorias (20)
- Campos obrigatórios: id, titulo, icone, resumo, base_legal, requisitos, documentos, passo_a_passo, dicas, valor, onde, links, tags
- Base legal completa: lei + artigo + URL HTTPS
- Listas não vazias: passo_a_passo, links (obrigatórios)
- Tags, requisitos, dicas (recomendados)

#### 🚗 Dropdown IPVA (27 estados)
- Todos 27 UFs presentes: AC a TO
- Campos por estado: uf, lei, art, sefaz
- URLs SEFAZ em HTTPS

#### 🔍 Matching Engine
- Termos uppercase (92 encontrados)
- Keywords por categoria (≥3 recomendado)
- Sinônimos mapeados
- Keywords lowercase

#### 📄 Documentos Mestre (16)
- Campos: id, nome, descricao, categorias
- Categorias referenciadas existem
- Relacionamentos bidirecionais

#### 🔗 Relacionamentos
- 88 relações via documentos_mestre
- Consistência bidirecional

#### 💻 Padrões de Código
- ❌ Sem alert() (usar showToast)
- ✅ Error handling presente
- ✅ 50 atributos ARIA
- ✅ VLibras carregado

#### 📝 Conteúdo Semântico
- Resumos informativos (>30 chars)
- Dicas úteis (>20 chars)
- Valores monetários atualizados
- Disclaimer completo

**Saída:**
```
Total de validações: 85
✅ Passou: 78 (91.8%)
⚠️ Avisos: 7 (8.2%)
❌ Erros: 0 (0%)

⚠️ VALIDAÇÃO PASSOU COM AVISOS
```

---

### 2. `codereview/codereview.py`

**Quality Gate com 16 categorias**

```bash
python3 codereview/codereview.py
```

**Categorias avaliadas:**
- LGPD / Privacidade
- Segurança
- Qualidade de Software
- Confiabilidade
- Performance
- Transparência / Fontes
- Versionamento
- Modularidade
- Acessibilidade
- Instituições de Apoio
- Dados Sensíveis
- Higiene de Arquivos
- Documentação
- Disclaimer / Regulatório
- WAF 5 Pilares
- Schema / Governança

**Score atual:** 100.0/100

---

### 3. `scripts/validate_sources.py`

**Valida links externos (gov.br, planalto.gov.br)**

```bash
python3 scripts/validate_sources.py
```

**O que faz:**
- Testa HTTP status (200 OK)
- Verifica domínios oficiais
- Timeout: 10s por URL
- Relatório: sucessos, timeouts, erros

⚠️ **Nota:** Pode demorar (~60-180s) por fazer requisições HTTP reais.

---

### 4. `scripts/quality_pipeline.py` ⭐ NOVO

**Orquestrador completo com 10 passos**

```bash
# Pipeline completo (produção)
python3 scripts/quality_pipeline.py --full

# Pipeline rápido (pre-commit)
python3 scripts/quality_pipeline.py --quick

# Pipeline CI/CD (sem testes manuais)
python3 scripts/quality_pipeline.py --ci
```

**10 Passos:**

1. **Limpeza** (0.1s)
   - Remove .backup, __pycache__, temp files

2. **Sintaxe** (0.1s)
   - JSON: direitos.json, matching_engine.json, manifest.json
   - HTML: estrutura básica
   - JavaScript: syntax check (se Node.js disponível)

3. **Fontes** (60-180s)
   - validate_sources.py
   - Gov.br links

4. **Quality Gate** (0.2s)
   - codereview.py
   - Score ≥75/100

5. **Análise 360°** (0.1s)
   - analise360.py (opcional)

6. **Acessibilidade** (0.1s)
   - ARIA attributes (≥40)
   - VLibras widget
   - Keyboard navigation
   - Focus styles

7. **Segurança** (0.1s)
   - CSP presente
   - URLs HTTPS
   - Dados sensíveis

8. **Performance** (0.1s)
   - HTML <50KB
   - JS <100KB
   - JSON <150KB

9. **Testes Browser** (manual)
   - Checklist 60+ testes
   - IPVA dropdown crítico

10. **Relatório Final**
    - JSON: quality_report.json
    - Scores, duração, falhas

**Duração:**
- `--full`: ~3-5min (com sources validation)
- `--quick`: ~30s (apenas sintaxe + quality gate)
- `--ci`: ~3min (sem testes manuais)

**Saída:**
```json
{
  "timestamp": "2026-02-12T23:27:01",
  "mode": "full",
  "steps": [
    {
      "name": "1.1 Remover arquivos .backup",
      "command": "find . -name \"*.backup\" -type f -delete",
      "duration": 0.041529,
      "success": true,
      "required": false
    }
  ]
}
```

---

## 🔒 Pre-Commit Hook

### Instalação

```bash
# Configurar Git para usar .githooks/
git config core.hooksPath .githooks

# Verificar
git config core.hooksPath
# Deve mostrar: .githooks
```

### O que faz

Executa automaticamente ANTES de cada commit:

1. ✅ Limpeza (backups, cache)
2. ✅ Sintaxe JSON + HTML
3. ✅ Conteúdo (validate_content.py)
4. ✅ Quality Gate (score ≥75)
5. ✅ Segurança (HTTPS, dados sensíveis)
6. ✅ Performance (tamanhos de arquivos)

### Bloqueio

Se QUALQUER validação falhar, o commit é **BLOQUEADO**:

```
[23:45:12] ❌ ✗ Conteúdo (categorias, IPVA, matching engine) falhou
[23:45:12] ❌   Erro: 3 erros encontrados

🛑 COMMIT BLOQUEADO - Corrija os erros acima
```

### Bypass (NÃO RECOMENDADO)

```bash
# Força commit mesmo com erros
git commit --no-verify -m "mensagem"
```

⚠️ **Use apenas em emergências!** Pode quebrar produção.

---

## 🤖 GitHub Actions CI/CD

### Workflow: `.github/workflows/quality-gate.yml`

**Triggers:**
- Push para `main` ou `develop`
- Pull requests para `main`
- Execução manual (workflow_dispatch)

**Steps:**

1. **Checkout** código
2. **Setup** Python 3.11
3. **Limpeza** (backups, cache)
4. **Sintaxe** JSON + HTML
5. **Conteúdo** (validate_content.py) ⭐ NOVO
6. **Quality Gate** (score ≥75)
7. **Segurança** (HTTPS, dados sensíveis)
8. **Performance** (tamanhos)
9. **Relatório** (upload artifact)

**Resultado:**

```
✅ TODAS VALIDAÇÕES PASSARAM!
🎉 Código pronto para merge/deploy
```

**Download relatório:**
- Actions → Quality Gate → Artifact: `quality-report`
- Retenção: 30 dias

---

## 📝 Ordem de Execução

### Pre-Commit (local, ~30s)

```bash
# Automático ao fazer commit
git add .
git commit -m "feat: nova funcionalidade"

# Executa:
1. Limpeza
2. Sintaxe
3. Conteúdo
4. Quality Gate
5. Segurança
6. Performance

# Se passou ✅ → commit prossegue
# Se falhou ❌ → commit bloqueado
```

### Pipeline Completo (pre-deploy, ~3-5min)

```bash
python3 scripts/quality_pipeline.py --full

# Executa todos 10 passos
# Gera quality_report.json
# Requer testes manuais (browser)
```

### CI/CD (GitHub Actions, ~2-3min)

```bash
# Automático ao push/PR
git push origin main

# Executa:
1. Limpeza
2. Sintaxe
3. Conteúdo ⭐
4. Quality Gate
5. Segurança
6. Performance
7. Relatório

# Se passou ✅ → permite merge
# Se falhou ❌ → bloqueia PR
```

---

## 🐛 Troubleshooting

### Erro: "KEYWORD_MAP não encontrado"

**Causa:** matching_engine.json usa estrutura alternativa

**Solução:** É um aviso, não erro. Estrutura atual usa "uppercase_only_terms" + categorias mapeadas.

---

### Erro: "URL não-HTTPS"

**Causa:** Link HTTP encontrado em base_legal ou links

**Solução:**
```bash
# Procurar URLs HTTP
grep -r "http://" data/direitos.json

# Corrigir manualmente para https://
```

---

### Erro: "base_legal incompleta (falta lei ou artigo)"

**Causa:** Entrada sem campo "lei" ou "artigo"

**Exemplo:**
```json
{
  "lei": "Portaria MEC nº 389/2013 — SISU",
  "url": "https://sisu.mec.gov.br"
  // ❌ Falta campo "artigo"
}
```

**Solução:**
```json
{
  "lei": "Portaria MEC nº 389/2013 — SISU",
  "artigo": "Art. 1º",
  "url": "https://sisu.mec.gov.br"
}
```

---

### Erro: "Pipeline timeout (especialmente validate_sources.py)"

**Causa:** Sites gov.br lentos ou temporariamente indisponíveis

**Solução:**
```bash
# Modo quick (pula sources validation)
python3 scripts/quality_pipeline.py --quick

# Ou aumentar timeout em quality_pipeline.py
# Linha ~50: timeout=300 → timeout=600
```

---

### Erro: "node: command not found" (JavaScript validation)

**Causa:** Node.js não instalado

**Impacto:** NON-CRITICAL (JavaScript já validado pelo browser)

**Solução (opcional):**
```bash
# macOS
brew install node

# Verificar
node --version
```

---

### Commit bloqueado mas sei que está correto

**Bypass (USE COM CUIDADO):**
```bash
git commit --no-verify -m "mensagem"
```

**Ou desabilitar temporariamente:**
```bash
# Desabilitar hooks
git config core.hooksPath ""

# Commit
git commit -m "mensagem"

# Reabilitar hooks
git config core.hooksPath .githooks
```

---

## 📊 Checklist Pre-Deploy

Use antes de fazer deploy em produção:

```bash
# 1. Pipeline completo
python3 scripts/quality_pipeline.py --full

# 2. Validação de conteúdo
python3 scripts/validate_content.py

# 3. Quality gate
python3 codereview/codereview.py

# 4. Testes manuais (browser)
open http://localhost:3000
# Seguir docs/QUALITY_TESTING_GUIDE.md

# 5. Verificar score
# Quality Gate ≥75: ✅
# WAF 5 Pillars 100%: ✅
# 0 erros críticos: ✅

# 6. Commit e push
git add .
git commit -m "release: v1.5.0"
git push origin main
```

---

## 🏆 Melhores Práticas

### 1. Commit Frequente

```bash
# Commits pequenos passam validação mais rápido
git add direitos.json
git commit -m "feat: adicionar categoria X"
```

### 2. Testar Antes de Commit

```bash
# Validar antes de commitar
python3 scripts/validate_content.py

# Se passou, commita
git commit -m "mensagem"
```

### 3. Seguir Padrões

```json
// ✅ BOM
{
  "id": "nova_categoria",
  "titulo": "Nova Categoria",
  "icone": "🎯",
  "resumo": "Descrição completa com mais de 30 caracteres",
  "base_legal": [
    {
      "lei": "Lei 12.345/2020",
      "artigo": "Art. 5º",
      "url": "https://planalto.gov.br/..."
    }
  ],
  "links": [
    {
      "titulo": "Site Oficial",
      "url": "https://exemplo.gov.br"
    }
  ]
}

// ❌ RUIM
{
  "id": "nova",
  "resumo": "Curto",
  "base_legal": [{"url": "http://site.com"}],
  "links": []
}
```

### 4. Documentar Mudanças

```bash
# Atualizar CHANGELOG.md sempre
## [1.5.1] - 2026-02-12
### Adicionado
- Nova categoria X com 10 campos
```

---

## 📚 Referências

- [QUALITY_TESTING_GUIDE.md](QUALITY_TESTING_GUIDE.md) — 60+ testes manuais
- [CHANGELOG.md](../CHANGELOG.md) — Histórico de versões
- [SECURITY.md](../SECURITY.md) — Política de segurança
- [GOVERNANCE.md](../GOVERNANCE.md) — Governança do projeto

---

## 🆘 Suporte

Issues ou dúvidas:
- GitHub Issues: [fabiotreze/nossodireito/issues](https://github.com/fabiotreze/nossodireito/issues)
- Email: fabiotreze@hotmail.com

---

**Última atualização:** 2026-02-12 (v1.8.0)
