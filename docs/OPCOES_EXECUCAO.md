# 🚀 OPÇÕES DE EXECUÇÃO — O Que Mais Podemos Executar?

**Data:** 12/02/2026
**Status:** 100% Master Compliance + 7 correções de acessibilidade aplicadas

---

## ✅ JÁ EXECUTADO HOJE

| Script | Status | Resultado | Próxima Execução |
|--------|--------|-----------|------------------|
| `master_compliance.py` | ✅ | 100% (959.9/959.9) | Diário |
| `analise360.py` | ✅ | 22/25 completos (88%) | Diário |
| `complete_beneficios.py` | ✅ | 0 modificações (já OK) | Quando houver parciais |
| `fix_accessibility_p0.py` | ✅ | 7 correções aplicadas | Já concluído |
| `validate_all.py` | ✅ | 5/6 OK (83.3%) | Diário |
| `audit_automation.py` | ✅ | Relatório gerado | Mensal |

---

## 🔄 OPÇÕES EXECUTÁVEIS AGORA

### **CATEGORIA 1: Validação & Qualidade** ⏱️ 2-5 min cada

#### 1.1 Master Compliance (revalidar)
```bash
python scripts/master_compliance.py
```
**Quando:** Sempre que modificar código/dados
**Esperado:** 100% (959.9/959.9)
**Status atual:** ✅ 100%

---

#### 1.2 Análise 360° (cobertura)
```bash
python scripts/analise360.py
```
**Quando:** Após modificar benefícios
**Esperado:** 22-25/25 completos, 80.6% cobertura
**Status atual:** ✅ 22/25 (88%)

---

#### 1.3 Validação Geral (todas rotinas)
```bash
python scripts/validate_all.py
```
**Quando:** Antes de commit
**Esperado:** 5/6 OK (timeout esperado)
**Status atual:** ✅ 5/6 OK (83.3%)

---

#### 1.4 Validação de Fontes (URLs)
```bash
python scripts/validate_govbr_urls.py
python scripts/validate_legal_sources.py
```
**Quando:** Semanal (valida links gov.br)
**Tempo:** ~1-2 min
**Status:** ⚠️ Timeout (60s+) - links muito lentos

---

### **CATEGORIA 2: Correções & Melhorias** ⏱️ 15 min - 4h

#### 2.1 Completar Benefícios Parciais (manual)
```bash
# Editar manualmente em data/direitos.json
# Benefícios parciais: ciptea, sus_terapias, transporte
```
**Status:** 22/25 completos (meta 20 atingida)
**Meta 100%:** Completar 3 parciais restantes
**Esforço:** ~30-60 min manual

**Gaps identificados:**
- `ciptea`: Campos vazios/curtos
- `sus_terapias`: Campos vazios/curtos
- `transporte`: Campos vazios/curtos

---

#### 2.2 Correções P2 de Acessibilidade (opcional)

**2.2.1 Link redundante** ⏱️ 15 min
```bash
# Criar script: scripts/fix_accessibility_p2_link.py
```
**Problema:** 1 link redundante (WAVE)
**Solução:** Adicionar `aria-hidden="true"` em duplicata
**Prioridade:** 🟢 BAIXA (não obrigatório, mas fácil)

**2.2.2 Contraste AAA** ⏱️ 4h
```bash
# Criar script: scripts/fix_accessibility_p2_contrast.py
```
**Problema:** 78 combinações com contraste < 7:1 (AAA)
**Solução:** Ajustar cores para contraste ≥7:1
**Prioridade:** 🟢 BAIXA (não obrigatório, AAA é opcional)

---

### **CATEGORIA 3: Novos Scripts (P0 Automação)** ⏱️ 4-8h cada

#### 3.1 Backup Automático
```bash
# Criar: scripts/auto_backup.py
```
**Função:** Backup diário automático com versionamento
**Esforço:** 4h
**Prioridade:** 🔴 P0 (prevenir perda de dados)
**Status:** 🔜 NÃO IMPLEMENTADO

---

#### 3.2 Validação de Base Legal
```bash
# Criar: scripts/validate_legal_compliance.py
```
**Função:** Scraping de planalto.gov.br para validar base legal
**Esforço:** 8h
**Prioridade:** 🔴 P0 (prevenir informações desatualizadas)
**Status:** 🔜 NÃO IMPLEMENTADO

---

### **CATEGORIA 4: Testes & CI/CD** ⏱️ 6-16h

#### 4.1 Testes Unitários
```bash
# Criar: tests/test_*.py
pytest tests/ --cov
```
**Função:** Testes automatizados com pytest
**Esforço:** 16h
**Prioridade:** 🟡 P1 (prevenir bugs)
**Status:** 🔜 NÃO IMPLEMENTADO

---

#### 4.2 JSON Schema Validation
```bash
# Criar: schemas/direitos.schema.json
python scripts/validate_schema.py
```
**Função:** Validação formal de estrutura JSON
**Esforço:** 6h
**Prioridade:** 🟡 P1 (prevenir estrutura divergente)
**Status:** 🔜 NÃO IMPLEMENTADO

---

#### 4.3 GitHub Actions (CI/CD)
```yaml
# Criar: .github/workflows/validation.yml
```
**Função:** Validação automática em cada commit
**Esforço:** 12h
**Prioridade:** 🟢 P2 (automação CI/CD)
**Status:** 🔜 NÃO IMPLEMENTADO

---

## 🎯 RECOMENDAÇÕES PRIORIZADAS

### **AGORA (Esta semana)** ⏱️ ~1h

1. ✅ **Completar 3 benefícios parciais** (manual)
   - Editar `data/direitos.json`
   - Preencher campos vazios: ciptea, sus_terapias, transporte
   - Validar com `python scripts/analise360.py`
   - **Meta:** 25/25 completos (100%)

2. ✅ **Criar script P2: Link redundante** (opcional)
   - Criar `scripts/fix_accessibility_p2_link.py`
   - Identificar link duplicado
   - Adicionar `aria-hidden="true"`
   - **Meta:** AccessMonitor ≥9.2/10

---

### **Próxima semana** ⏱️ 4h

3. 🔴 **Implementar backup automático** (P0)
   - Criar `scripts/auto_backup.py`
   - Backup diário de `data/` e `docs/`
   - Versionamento com Git tags
   - **Meta:** Zero perda de dados

---

### **Mês 1** ⏱️ 20h

4. 🔴 **Validação de base legal** (P0) - 8h
5. 🟡 **JSON Schema** (P1) - 6h
6. 🟡 **Testes unitários** (P1) - 16h (parcial)

---

### **Mês 2-3** ⏱️ ~30h

7. 🟢 **GitHub Actions** (P2) - 12h
8. 🟢 **Contraste AAA** (P2) - 4h
9. 🟢 **Dashboard métricas** (P3) - 20h

---

## 📊 STATUS GERAL

### **Compliance & Qualidade**

| Métrica | Atual | Meta | Status |
|---------|-------|------|--------|
| **Master Compliance** | 100% | 100% | ✅ PERFEITO |
| **Benefícios completos** | 22/25 (88%) | 25/25 (100%) | ⚠️ FALTAM 3 |
| **Cobertura** | 80.6% | ≥75% | ✅ ATINGIDA |
| **Acessibilidade (P0)** | ~95% | ≥95% | ✅ CORRIGIDO |
| **Validação geral** | 5/6 (83%) | 6/6 (100%) | ⚠️ 1 TIMEOUT |

---

### **Automação**

| Área | Status | Prioridade | Esforço |
|------|--------|------------|---------|
| **Master Compliance** | ✅ Automatizado | - | 0h |
| **Análise 360** | ✅ Automatizado | - | 0h |
| **Validação geral** | ✅ Automatizado | - | 0h |
| **Backup** | ❌ Não automatizado | 🔴 P0 | 4h |
| **Base legal** | ❌ Não automatizado | 🔴 P0 | 8h |
| **Testes unitários** | ❌ Não implementado | 🟡 P1 | 16h |
| **JSON Schema** | ❌ Não implementado | 🟡 P1 | 6h |
| **CI/CD** | ❌ Não implementado | 🟢 P2 | 12h |

---

## 🚀 PRÓXIMO COMANDO RECOMENDADO

### **Opção 1: Completar benefícios (manual)** ⏱️ 30-60 min

```bash
# 1. Abrir arquivo
code data/direitos.json

# 2. Buscar benefícios parciais:
#    - ciptea
#    - sus_terapias
#    - transporte

# 3. Preencher campos vazios:
#    - requisitos (≥5)
#    - documentos (≥4)
#    - passos (≥6)
#    - dicas (≥4)
#    - links (≥2)
#    - base_legal (≥1)
#    - valor (≥10 chars)

# 4. Validar
python scripts/analise360.py

# 5. Confirmar 100%
# Esperado: 25/25 completos (100%)
```

---

### **Opção 2: Criar script P2 (link redundante)** ⏱️ 15 min

```bash
# Criar scripts/fix_accessibility_p2_link.py
code scripts/fix_accessibility_p2_link.py

# Executar
python scripts/fix_accessibility_p2_link.py

# Validar online
# AccessMonitor: https://accessmonitor.acessibilidade.gov.pt/
```

---

### **Opção 3: Revalidar tudo** ⏱️ 2 min

```bash
python scripts/validate_all.py
```

---

## 📋 CHECKLIST RÁPIDO

### **Diário (antes de commit):**
- [ ] `python scripts/validate_all.py`
- [ ] `python scripts/master_compliance.py`
- [ ] Verificar output (deve ser 100%)

### **Semanal:**
- [ ] `python scripts/analise360.py`
- [ ] Validar fontes gov.br (manual)
- [ ] Backup manual (até implementar auto_backup.py)

### **Mensal:**
- [ ] `python scripts/audit_automation.py`
- [ ] Validar acessibilidade online (3 tools)
- [ ] Revisar documentação

---

## 🎯 META FINAL: 100% EM TUDO

| Item | Atual | Meta | Ação |
|------|-------|------|------|
| Master Compliance | 100% | 100% | ✅ MANTIDO |
| Benefícios | 88% | **100%** | 🔧 COMPLETAR 3 |
| Acessibilidade | ~95% | ≥95% | ✅ ATINGIDO |
| Automação | 40% | ≥80% | 🔧 IMPLEMENTAR P0+P1 |

---

**💡 Recomendação imediata:** Completar os 3 benefícios parciais manualmente (30-60 min) para atingir **100% em benefícios (25/25)**.

---

**Última atualização:** 12/02/2026 14:45
**Próxima revisão:** Diário (validate_all.py)
