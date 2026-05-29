# Scripts de Dados — Classificação e Status

**Versão:** 1.0  
**Atualizado:** 2026-05-29

---

## 📊 Resumo

5 scripts de **enriquecimento de dados** em `scripts/`:

| Script | Tipo | Uso | Status | Manutentor |
|---|---|---|---|---|
| `classify_aplicabilidade.py` | Data enrichment | Manual ou periódico | ✅ **MANTER** | @dev |
| `classify_consulta_especializada.py` | Data enrichment | Manual ou periódico | ✅ **MANTER** | @dev |
| `enrich_cids_canonicos.py` | Data enrichment | Manual ou periódico | ✅ **MANTER** | @dev |
| `migrate_categoria_metadata.py` | One-off migration | Executado 2026-05 | ⚠️ **MANTER (histórico)** | @dev |
| `prerender_direitos.py` | Static SEO pre-rendering | Manual e opcional | ✅ **MANTER (opcional)** | @dev |

---

## 🟢 MANTER — Scripts de Enriquecimento de Dados

### 1. `classify_aplicabilidade.py`

**Objetivo:** Classifica cada categoria no `data/direitos.json` pelo tipo de direito.

**Política determinística:**
```python
# 4 valores possíveis (enum):
- condicao_medica          # restrito por CIDs
- documento_administrativo # é documento, não condição
- publico_fechado          # grupo legal específico (talidomida, etc)
- servico_universal        # atende qualquer PcD
```

**Uso:**
```bash
# Aplicar e salvar
python scripts/classify_aplicabilidade.py

# Dry-run (mostra mudanças sem salvar)
python scripts/classify_aplicabilidade.py --dry-run
```

**Trigger:** Manual ou em PR que adiciona categoria nova.

**Razão de manter:** Regras em código (versionado) garantem consistência. Precisa reexecução se schema muda ou nova categoria adicionada.

---

### 2. `classify_consulta_especializada.py`

**Objetivo:** Classifica se direito requer consulta especializada (Defensoria, CRAS, etc).

**Uso:**
```bash
python scripts/classify_consulta_especializada.py  # aplica e salva
python scripts/classify_consulta_especializada.py --dry-run
```

**Coerência:** Coordenado com `classify_aplicabilidade.py` (issue #193, PR #201).

**Razão de manter:** Aplicação de regras jurídicas determinísticas, versionadas.

---

### 3. `enrich_cids_canonicos.py`

**Objetivo:** Preenche CIDs canônicos (OMS, públicos) para categorias do tipo `publico_fechado`.

**Uso:**
```bash
python scripts/enrich_cids_canonicos.py  # aplica e salva
```

**Razão de manter:** Dados médicos precisam de manutenção periódica se OMS atualizar CID-10.

---

## ⚠️ MANTER (Histórico) — One-Off Migration

### 4. `migrate_categoria_metadata.py`

**Objetivo:** One-off migration executado para PR #200 (schema v1.28.0).

**Mudança:** Adicionou `data_ultima_verificacao` + `canal_de_atendimento_oficial` ao schema.

**Status:** Script já executado. Pode ser mantido como referência histórica.

**Recomendação:** Mover para `scripts/archive/migrations/` (baixa prioridade) ou deixar como está.

---

## ✅ MANTER (Opcional) — Pre-render SEO

### 5. `prerender_direitos.py`

**Objetivo:** Gera páginas HTML estáticas por categoria em `direitos/<slug>/index.html` e regenera `sitemap.xml` para indexação SEO.

**Histórico:** Última atualização em feat #138 (v1.28.0, 2024-11).

**Status:** Script documentado no `README.md`, em `docs/ARCHITECTURE.md` e no próprio cabeçalho do arquivo. Não roda no deploy atual, mas continua útil como recurso opcional para restaurar páginas profundas de SEO.

**Uso:**
```bash
python3 scripts/prerender_direitos.py
python3 scripts/prerender_direitos.py --check
```

**Recomendação:** 
- [x] Manter como script opcional, fora do fluxo padrão de deploy
- [ ] Se voltar para produção: ligar passo no `deploy.yml`
- [ ] Se voltar para produção: regenerar `sitemap.xml` junto com o deploy

**Ação:** Não deletar. Apenas decidir separadamente se vale reativar no pipeline.

---

## 🎯 Proposta: Automatizar Enriquecimento Periódico

Para `classify_*.py` e `enrich_cids_canonicos.py`, criar **workflow automático**:

```yaml
# .github/workflows/data-enrichment-schedule.yml (novo)
name: Data Enrichment (Periodic)

on:
  schedule:
    - cron: "0 9 * * 1"  # Toda segunda, 09:00 UTC

jobs:
  enrich:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Run enrichment scripts
        run: |
          python scripts/classify_aplicabilidade.py
          python scripts/classify_consulta_especializada.py
          python scripts/enrich_cids_canonicos.py
      
      - name: Validate changes
        run: npm run validate
      
      - name: Create PR if changes
        if: ${{ success() }}
        run: |
          if ! git diff-index --quiet HEAD --; then
            git checkout -b chore/auto-enrich-$(date +%Y%m%d)
            git add data/direitos.json data/dicionario_pcd.json
            git commit -m "chore: enriquecimento automático de dados"
            git push origin
            gh pr create --auto-merge --title "chore: enriquecimento automático" ...
          fi
```

---

## 📋 Checklist de Documentação

- [x] Scripts de enriquecimento classificados
- [x] Razões de manter documentadas
- [x] Triggers (manual/periódico/workflow) clarificados
- [ ] Adicionar descrição de cada script em `README.md`
- [ ] Adicionar exemplos de execução em docs
- [x] Classificar `prerender_direitos.py` como opcional, não órfão

---

## 🔗 Referências

- Issue #193 (schema + classificações)
- Issue #138 (v1.28.0, histórico)
- PR #207 (enriquecimento coordenado)
- PR #201 (requer_consulta_especializada)
