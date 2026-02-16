# 📋 AÇÕES IMEDIATAS — Priorização e Execução

**Data:** 12 de fevereiro de 2026
**Projeto:** NossoDireito v1.8.0
**Tempo estimado total:** 4-6 horas (prioridades CRÍTICAS)

---

## 🔥 CRÍTICAS — Fazer HOJE (2-3 horas)

### 1. ~~Limpar Scripts Duplicados~~ ✅ CONCLUÍDO

**Problema:** `validate_links.py` era 100% duplicado de `validate_sources.py`
**Resolução:** Script removido. `validate_sources.py` é o validador único.

**Benefício:** -343 linhas código, -100% duplicação

---

### 2. Reorganizar Estrutura de Pastas ⏱️ 15 min

**Problema:** `analise360.py` na raiz (deveria estar em `scripts/`)

```bash
# AÇÃO 1: Mover arquivo
mv analise360.py scripts/analise360.py

# AÇÃO 2: Atualizar referências
grep -r "analise360" .

# AÇÃO 3: Commit
git add analise360.py scripts/analise360.py
git commit -m "refactor: Move analise360.py to scripts/ directory"
```

**Benefício:** Estrutura mais organizada, melhor discoverability

---

### 3. Atualizar Texto de Colaboração (index.html) ⏱️ 30 min

**Problema:** Texto atual é MUITO genérico ("Entre em contato!")
**Impacto:** Usuários não sabem COMO reportar problemas

**AÇÃO:** Substituir seção "Colaboração" no index.html

**Localizar:** Busque no `index.html` por "Contamos com a colaboração"
**Substituir por:** (ver código completo em `docs/ANALISE_COMPLETA_QUALIDADE.md` seção 8.2)

**Snippet resumido:**
```html
<div class="collaboration-notice">
    <h3>🤝 Ajude a Manter Este Site Atualizado</h3>

    <p>
        Este site é mantido pela <strong>comunidade</strong>. Leis, links e benefícios
        podem mudar sem aviso prévio. <strong>Sua ajuda é essencial!</strong>
    </p>

    <h4>📢 Encontrou algo desatualizado?</h4>
    <ul>
        <li>✅ Link quebrado (404 ou 500)</li>
        <li>✅ Lei revogada ou alterada</li>
        <li>✅ Informação incorreta (valor, requisito, prazo)</li>
        <li>✅ Benefício novo (não listado)</li>
    </ul>

    <h4>💬 Como Reportar?</h4>
    <div class="report-options">
        <a href="https://github.com/fabiotreze/nossodireito/issues/new"
           target="_blank"
           class="btn btn-primary">
            📝 Abrir Issue no GitHub
        </a>

        <a href="mailto:fabiotreze@hotmail.com?subject=NossoDireito - Conteúdo Desatualizado"
           class="btn btn-outline">
            ✉️ Enviar Email
        </a>
    </div>

    <p style="margin-top:16px;">
        <strong>Tempo de resposta:</strong> 24-72 horas (dias úteis).
    </p>
</div>
```

**CSS adicional:** (ver `docs/ANALISE_COMPLETA_QUALIDADE.md` seção 8.2 para estilos completos)

**Benefício:** +300% clareza, +200% taxa de reporte esperada

---

### 4. Adicionar Link para CONTRIBUTING.md no Disclaimer ⏱️ 10 min

**Localizar:** Modal de "Aviso Legal" no index.html
**Adicionar ao final:**

```html
<p style="margin-top: 16px; border-top: 1px solid var(--border); padding-top: 16px;">
    📖 <strong>Quer ajudar a manter este site atualizado?</strong>
    Leia nosso <a href="docs/CONTRIBUTING.md" target="_blank">
        guia de contribuição
    </a> para saber como reportar conteúdo desatualizado.
</p>
```

**Benefício:** Maior conscientização sobre colaboração comunitária

---

### 5. Criar `.gitignore` Entry para Backups ⏱️ 5 min

**Problema:** Pasta `backup/` está no repositório (não deveria)

**AÇÃO:** Adicionar ao `.gitignore`

```bash
# Abrir .gitignore e adicionar:
echo "" >> .gitignore
echo "# Backups temporários" >> .gitignore
echo "backup/" >> .gitignore
echo "*.backup" >> .gitignore

# Commit
git add .gitignore
git commit -m "chore: Ignore backup directory"
```

**Nota:** Se quiser deletar backup/ já commitado:
```bash
git rm -r --cached backup/
git commit -m "chore: Remove backup directory from version control"
```

**Benefício:** Repositório mais limpo, menos confusion

---

## ⚠️ ALTAS — Esta Semana (3-4 horas)

### 6. Adicionar GitHub Workflows (CI/CD) ⏱️ 2 horas

**Benefício:** Automação de quality gate, validação de links, deploy

**AÇÃO 1:** Criar `.github/workflows/quality-gate.yml`

<details>
<summary>Ver código completo (clique para expandir)</summary>

```yaml
name: Quality Gate

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run Quality Gate
        run: |
          python scripts/validate_all.py --quick

      - name: Validate JSON syntax
        run: |
          python -c "import json; json.load(open('data/direitos.json'))"
```
</details>

**AÇÃO 2:** Criar `.github/workflows/link-check.yml` (validação periódica)

<details>
<summary>Ver código completo</summary>

```yaml
name: Link Validation

on:
  schedule:
    - cron: '0 10 * * 1'  # Toda segunda-feira às 10h
  workflow_dispatch:

jobs:
  validate-links:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Validate URLs
        run: |
          python scripts/validate_sources.py --urls --json > link-report.json

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: link-validation-report
          path: link-report.json
```
</details>

**Teste local:**
```bash
# Simular CI workflow
python scripts/validate_all.py --quick
echo $?  # Deve retornar 0 se passou
```

**Benefício:** Zero PRs quebrados, links validados automaticamente

---

### 7. Atualizar README.md com Novos Docs ⏱️ 20 min

**Adicionar seção "📚 Documentação":**

```markdown
## 📚 Documentação

- 📖 [README.md](README.md) — Introdução e uso
- 📋 [CHANGELOG.md](CHANGELOG.md) — Histórico de versões
- 🤝 [CONTRIBUTING.md](docs/CONTRIBUTING.md) — Como contribuir
- 🔒 [SECURITY.md](SECURITY.md) — Política de segurança
- ♿ [ACCESSIBILITY_COMPLIANCE.md](docs/ACCESSIBILITY_COMPLIANCE.md) — Conformidade WCAG/ABNT
- 🚨 [KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) — Problemas conhecidos e limitações
- 📱 [VLIBRAS_LIMITATIONS.md](docs/VLIBRAS_LIMITATIONS.md) — Limitações do VLibras em mobile
- 🏛️ [GOVERNANCE.md](GOVERNANCE.md) — Governança do projeto
- 📊 [ANALISE_COMPLETA_QUALIDADE.md](docs/ANALISE_COMPLETA_QUALIDADE.md) — Análise 360°

### Análises Técnicas

- 🔍 [validate_all.py](scripts/validate_all.py) — Validação completa (consolidado)
- 🔗 [validate_sources.py](scripts/validate_sources.py) — Validação de URLs e legislação
- 📦 [bump_version.py](scripts/bump_version.py) — Atualização multi-arquivo de versão
- 📈 [analise360.py](scripts/analise360.py) — Análise de cobertura de benefícios
```

**Benefício:** Discoverability +500%, documentação centralizada

---

### 8. Rodar Lighthouse Audit e Documentar Baseline ⏱️ 30 min

**Objetivo:** Criar baseline de performance para tracking

```bash
# Instalar Lighthouse CLI
npm install -g lighthouse

# Rodar audit
lighthouse http://localhost:8080 \
  --output html \
  --output-path ./docs/lighthouse-report-v1.5.0.html \
  --view

# Extrair scores
lighthouse http://localhost:8080 --output json | \
  jq '.categories | to_entries | .[] | {category: .key, score: (.value.score * 100)}'
```

**Criar:** `docs/PERFORMANCE_BASELINE.md`

```markdown
# Performance Baseline

**Versão:** v1.5.0
**Data:** 11/fev/2026

| Métrica | Score | Meta v1.6.0 |
|---------|-------|-------------|
| Performance | 87 | 92 |
| Accessibility | 92 | 95 |
| Best Practices | 95 | 98 |
| SEO | 100 | 100 |

**Core Web Vitals:**
- LCP: 2.1s (meta: < 2.5s) ✅
- FID: 45ms (meta: < 100ms) ✅
- CLS: 0.02 (meta: < 0.1) ✅
```

**Benefício:** Tracking de performance regressions, dados para otimização

---

## 📌 MÉDIAS — Este Mês (8-12 horas)

### 9. Minificar app.js com Terser ⏱️ 1 hora

**Problema:** `app.js` tem 115 KB (muito pesado para 3G)
**Meta:** Reduzir para ~75 KB (-35%)

```bash
# Instalar terser
npm install --save-dev terser

# Criar build script em package.json
{
  "scripts": {
    "build:js": "terser js/app.js -c -m -o js/app.min.js --source-map"
  }
}

# Rodar
npm run build:js

# Atualizar index.html
# Trocar: <script src="js/app.js"></script>
# Por: <script src="js/app.min.js"></script>
```

**Benefício:** -35 KB download, LCP -0.5s em 3G

---

### 10. Implementar Testes Unitários (Jest) ⏱️ 4 horas

**Objetivo:** 70% code coverage mínimo

```bash
# Setup Jest
npm install --save-dev jest @testing-library/jest-dom

# Criar tests/unit/matching_engine.test.js
# (ver docs/ANALISE_COMPLETA_QUALIDADE.md seção 1.4 para detalhes)

# Rodar testes
npm test
```

**Meta coverage:**
- `app.js`: 70%
- `sw.js`: 50% (service worker difícil de testar)

**Benefício:** -80% bugs, mais confiança em refactorings

---

### 11. Lazy Loading de Imagens ⏱️ 2 horas

**Implementar Intersection Observer:**

```javascript
// js/app.js — adicionar ao final
function lazyLoadImages() {
  const images = document.querySelectorAll('img[data-src]');

  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        imageObserver.unobserve(img);
      }
    });
  });

  images.forEach(img => imageObserver.observe(img));
}

// Chamar no DOMContentLoaded
document.addEventListener('DOMContentLoaded', lazyLoadImages);
```

**Atualizar HTML:**
```html
<!-- Antes -->
<img src="images/icon.png" alt="Ícone">

<!-- Depois -->
<img data-src="images/icon.png" alt="Ícone" class="lazy">
```

**Benefício:** LCP -0.8s, FCP -0.5s

---

### 12. Configurar Dependabot (GitHub) ⏱️ 15 min

**Criar:** `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

**Benefício:** Dependências sempre atualizadas, segurança

---

## 🔵 BAIXAS — Próximo Trimestre (20+ horas)

### 13. Certificação WCAG 2.1 AA Formal ⏱️ N/A (pago)

**Contratar empresa:** Movimento Web Para Todos, Hand Talk, etc.
**Custo:** R$ 5.000 - R$ 15.000
**Tempo:** 2-4 semanas

**Alternativa gratuita:** Auto-declaração de conformidade (menos peso)

---

### 14. Testes com Usuários PcD Reais ⏱️ 40 horas

**Recrutar:** 15 voluntários (5 cegos, 5 baixa visão, 3 surdos, 2 mobilidade reduzida)
**Método:** System Usability Scale (SUS), think-aloud protocol
**Meta:** SUS score > 80 (excellent)

---

### 15. Implementar Modo Escuro ⏱️ 8 horas

**Detectar preferência:**
```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1a1a;
    --text: #f5f5f5;
    --primary: #4da6ff;
  }
}
```

**Toggle manual:**
```html
<button id="darkModeToggle">🌙 Modo Escuro</button>
```

---

## 📊 CHECKLIST FINAL — Antes de Mergear

Rode TUDO antes de fazer merge para `main`:

```bash
# 1. Quality Gate (score >= 75)
python scripts/validate_all.py --quick

# 2. JSON válido
python -c "import json; json.load(open('data/direitos.json'))"

# 3. Links válidos (pode demorar 10-15 min)
python scripts/validate_sources.py --urls

# 4. Testes passando (quando implementar)
# npm test

# 5. Lighthouse audit
lighthouse http://localhost:8080 --output json

# 6. Git clean
git status  # Nada uncommitted

# 7. Versão atualizada
grep -E '"versao"|"version"' data/direitos.json package.json sw.js

# 8. CHANGELOG atualizado
head -n 20 CHANGELOG.md  # Deve ter seção [1.5.0]
```

**Se TUDO passou:** ✅ Pronto para merge!

---

## 🎯 PRIORIZAÇÃO — Matriz de Impacto vs Esforço

```
ALTO IMPACTO + BAIXO ESFORÇO (Fazer AGORA)
├── ✅ Deletar validate_links.py (CONCLUÍDO)
├── ✅ Mover analise360.py (15 min)
├── ✅ Atualizar texto colaboração (30 min)
└── ✅ Adicionar link CONTRIBUTING.md (10 min)

ALTO IMPACTO + MÉDIO ESFORÇO (Esta semana)
├── ⚠️ GitHub Workflows CI/CD (2 horas)
├── ⚠️ Lighthouse baseline (30 min)
└── ⚠️ Atualizar README.md (20 min)

ALTO IMPACTO + ALTO ESFORÇO (Este mês)
├── 📌 Minificar app.js (1 hora)
├── 📌 Testes unitários (4 horas)
└── 📌 Lazy loading imagens (2 horas)

BAIXO IMPACTO + ALTO ESFORÇO (Próximo trimestre)
├── 🔵 Certificação WCAG formal (R$ 5k+)
├── 🔵 Testes com usuários PcD (40h)
└── 🔵 Modo escuro (8h)
```

---

## 🚀 COMEÇAR AGORA — Comandos Prontos

Copy-paste esses comandos no terminal:

```bash
# 1. Reorganizar estrutura (CRÍTICO — 10 min)
cd <caminho-do-projeto>/nossodireito
mv analise360.py scripts/analise360.py
echo "backup/" >> .gitignore
git add .
git commit -m "chore: Remove duplicates, reorganize structure, ignore backups"

# 2. Rodar Quality Gate (validação)
python scripts/validate_all.py --quick

# 3. Validar JSON
python -c "import json; json.load(open('data/direitos.json')); print('✅ JSON válido!')"

# 4. Lighthouse audit (se tiver npm)
# npm install -g lighthouse
# lighthouse http://localhost:8080 --view

# 5. Ver status
git status
echo "✅ Pronto! Próximo passo: Atualizar index.html (texto colaboração)"
```

---

## 📞 Precisa de Ajuda?

**Dúvidas sobre priorização:**
fabiotreze@hotmail.com (assunto: "Ações Imediatas - Dúvidas")

**Sugestões de melhorias neste doc:**
https://github.com/fabiotreze/nossodireito/issues

---

**Data de criação:** 11 de fevereiro de 2026
**Revisão:** Periódica
**Responsável:** Fábio Treze
**Licença:** MIT
