# 🚀 GUIA RÁPIDO — Como Usar as Validações

**Projeto:** NossoDireito
**Data:** 2026-02-12
**Status:** 100% Compliance | 40% Automação

---

## 📋 COMANDOS PRINCIPAIS

### 1. Validação Completa (Tudo de uma vez)

```bash
# Modo read-only (apenas validar)
python scripts/validate_all.py

# Modo auto-fix (validar + corrigir)
python scripts/validate_all.py --fix

# Com notificações (requer SLACK_WEBHOOK_URL)
python scripts/validate_all.py --notify

# Tudo junto
python scripts/validate_all.py --fix --notify
```

**Output:**
- Executa 7 fases de validação
- Gera `validation_report.json`
- Exit code 0 (OK) ou 1 (falhas)

---

### 2. Master Compliance (20 Categorias)

```bash
# Windows PowerShell
$env:PYTHONIOENCODING='utf-8'; python scripts/master_compliance.py

# Linux/Mac
PYTHONIOENCODING=utf-8 python scripts/master_compliance.py
```

**Output:**
- Score: X/973.9
- Relatório de cada categoria
- Tempo: ~1.5s

**Métricas:**
- ✅ 100% = PERFEITO
- ✅ ≥95% = EXCELENTE
- ⚠️ 90-95% = BOM
- ❌ <90% = PRECISA ATENÇÃO

---

### 3. Análise 360° (Cobertura + Completude)

```bash
python scripts/analise360.py
```

**Output:**
- Lista de benefícios (✅ completos | ⚠️ parciais)
- Cobertura total (% implementados)
- Completude (% completos)
- IPVA: 27 estados mapeados
- Gaps detalhados por benefício

**Métricas:**
- ✅ Cobertura: ≥75% = OK
- ✅ Completude: ≥20 completos = OK
- ✅ IPVA: 27 estados = OK

---

### 4. Completar Benefícios Automaticamente

```bash
python scripts/complete_beneficios.py
```

**O que faz:**
- Identifica benefícios parciais
- Preenche campos faltantes com templates
- Cria backup automático (`data/direitos.json.backup`)
- Salva alterações

**Campos preenchidos:**
- requisitos (mín. 5)
- documentos (mín. 4)
- passo_a_passo (mín. 6)
- dicas (mín. 4)
- links (mín. 2)

**⚠️ ATENÇÃO:** Revise o conteúdo gerado (templates genéricos)

---

### 5. Auditoria de Automação

```bash
python scripts/audit_automation.py
```

**Output:**
- `docs/AUTOMATION_AUDIT.md`
- Mapeia: automatizado vs não automatizado
- 8 recomendações priorizadas (P0-P3)
- Estimativa de esforço (~100h total)

---

### 6. Validação de Fontes (URLs .gov.br)

```bash
python scripts/validate_sources.py
```

**O que faz:**
- Verifica conectividade de URLs .gov.br
- Valida HTTP status (200 OK)
- Testa formato JSON de links

**⚠️ ATENÇÃO:** Pode demorar (~60s) devido a requests HTTP

---

## 🔄 WORKFLOW RECOMENDADO

### Desenvolvimento Diário

```bash
# 1. Antes de commitar
python scripts/master_compliance.py

# 2. Se score < 100%
#    → Corrigir problemas listados

# 3. Opcional: análise de conteúdo
python scripts/analise360.py

# 4. Commit
git add .
git commit -m "feat: descrição da mudança"
git push
```

---

### Manutenção Semanal

```bash
# 1. Validação completa
python scripts/validate_all.py --fix

# 2. Verificar relatório
cat validation_report.json

# 3. Se houver parciais, completar
python scripts/complete_beneficios.py

# 4. Revalidar
python scripts/master_compliance.py

# 5. Backup manual (até auto_backup.py estar pronto)
cp data/direitos.json backups/direitos_$(date +%Y-%m-%d).json
```

---

### Auditoria Mensal

```bash
# 1. Auditoria de automação
python scripts/audit_automation.py

# 2. Ler relatório
cat docs/AUTOMATION_AUDIT.md

# 3. Planejar próximas implementações (P0 → P3)

# 4. Atualizar CHANGELOG.md com melhorias
```

---

## 🐛 TROUBLESHOOTING

### Problema: "UnicodeDecodeError" (Emojis)

**Solução:**
```bash
# Windows PowerShell
$env:PYTHONIOENCODING='utf-8'; python script.py

# Linux/Mac
PYTHONIOENCODING=utf-8 python script.py

# Ou adicionar no script:
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

---

### Problema: "ModuleNotFoundError: No module named 'X'"

**Solução:**
```bash
# Instalar dependências
pip install -r requirements.txt

# Ou especificamente
pip install requests beautifulsoup4
```

---

### Problema: Master Compliance score < 100% (ANÁLISE 360 falha)

**Diagnóstico:**
```bash
# Executar analise360 standalone
python scripts/analise360.py

# Ver saída completa
# Verificar se output contém:
#   - "COBERTURA TOTAL (implementados): X.X%"
#   - "Implementados completos: X/31"
#   - "Arquivo: 27 estados mapeados"
```

**Solução:**
- Se output OK mas master falha: verificar regex em `master_compliance.py` linha 1760-1815
- Se output vazio: adicionar `if __name__ == '__main__': main()` no final do script

---

### Problema: validate_sources.py timeout

**Solução:**
```bash
# Aumentar timeout no validate_all.py linha ~100
timeout=120  # De 60 para 120 segundos

# Ou rodar standalone (sem timeout)
python scripts/validate_sources.py
```

---

### Problema: Backup não criado automaticamente

**Status:** `auto_backup.py` ainda não implementado (P0)

**Solução temporária:**
```bash
# Backup manual
cp data/direitos.json data/direitos.json.backup

# Ou com timestamp
cp data/direitos.json "backups/direitos_$(date +%Y%m%d_%H%M%S).json"
```

---

## 📊 INTERPRETANDO RESULTADOS

### Master Compliance

```
📊 SCORE FINAL: XXX.X/973.9 = YY.Y%
```

- **100%:** PERFEITO! ✅
- **99-99.9%:** EXCELENTE, pequenos ajustes
- **95-98.9%:** BOM, alguns pontos a melhorar
- **90-94.9%:** ATENÇÃO, correções necessárias
- **<90%:** CRÍTICO, problemas sérios

**Categorias abaixo de 100%:**
- Listar quais falharam
- Ver mensagens de erro específicas
- Corrigir um por um

---

### Análise 360°

```
🎯 COBERTURA TOTAL (implementados): 80.6%
✨ COMPLETUDE (benefícios completos): 71.0%
📊 Arquivo: 27 estados mapeados
```

**Cobertura:**
- ✅ ≥75%: OK
- ⚠️ 60-74%: BOM
- ❌ <60%: Implementar mais benefícios

**Completude:**
- ✅ ≥20 completos: OK
- ⚠️ 15-19: BOM
- ❌ <15: Auto-completar via `complete_beneficios.py`

**IPVA:**
- ✅ 27 estados: COMPLETO
- ⚠️ 20-26: BOM
- ❌ <20: Atualizar `ipva_pcd_estados.json`

---

### validate_all.py

```
✅ Passed: 5/6 (83.3%)
```

**Resultado:**
- ✅ 100%: PERFEITO
- ✅ ≥80%: EXCELENTE
- ⚠️ 60-79%: BOM
- ❌ <60%: CRÍTICO

**Falhas:**
- Ver lista de falhas no output
- Checar `validation_report.json` para detalhes
- Corrigir scripts que falharam

---

## 🎯 QUANDO USAR CADA SCRIPT

| Situação | Script | Quando Rodar |
|----------|--------|--------------|
| **Daily dev** | `master_compliance.py` | Antes de commitar |
| **Weekly check** | `validate_all.py` | Início da semana |
| **Content update** | `analise360.py` | Após adicionar/editar benefícios |
| **Quality fix** | `complete_beneficios.py` | Quando completude < 20 |
| **Planning** | `audit_automation.py` | Mensal ou quando planejar melhorias |
| **URL check** | `validate_sources.py` | Após adicionar links .gov.br |

---

## 🔮 PRÓXIMOS COMANDOS (Quando Implementados)

### auto_backup.py (P0 - 4h)

```bash
# Backup diário automático
python scripts/auto_backup.py

# Cron job (Linux/Mac)
0 23 * * * /usr/bin/python3 /path/scripts/auto_backup.py

# Windows Task Scheduler
# Criar task: Daily 23:00, Action: python scripts/auto_backup.py
```

---

### validate_legal_compliance.py (P0 - 8h)

```bash
# Validar base legal de todos os benefícios
python scripts/validate_legal_compliance.py

# Verificar benefício específico
python scripts/validate_legal_compliance.py --beneficio bpc

# Auto-fix (atualizar leis revogadas)
python scripts/validate_legal_compliance.py --fix
```

---

### validate_content.py (P1 - 12h)

```bash
# Validar conteúdo semântico
python scripts/validate_content.py

# Verificar gramática
python scripts/validate_content.py --grammar

# Detectar datas antigas
python scripts/validate_content.py --dates
```

---

### GitHub Actions (P2 - 12h)

```yaml
# .github/workflows/daily_validation.yml
# Roda automaticamente todo dia 00:00 UTC
# Notifica Slack em falhas
```

**Uso:**
- Automático (cron)
- Ou manual: GitHub → Actions → Run workflow

---

## 📚 DOCUMENTAÇÃO ADICIONAL

- **Conquista de 100%:** `docs/ACHIEVEMENT_100_PERCENT_FINAL.md`
- **Auditoria de Automação:** `docs/AUTOMATION_AUDIT.md`
- **Status de Rotinas:** `docs/VALIDATION_ROUTINES_STATUS.md`
- **Resumo Final:** `docs/RESUMO_FINAL_100_PERCENT.md`

---

## ⚡ ATALHOS ÚTEIS (PowerShell)

### Adicionar ao $PROFILE

```powershell
# C:\Users\<USER>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1

# Função para rodar master compliance
function Validate-NossoDireito {
    $env:PYTHONIOENCODING='utf-8'
    python C:\path\to\nossodireito\scripts\master_compliance.py
}
Set-Alias nv Validate-NossoDireito

# Função para validação completa
function Validate-All-NossoDireito {
    $env:PYTHONIOENCODING='utf-8'
    python C:\path\to\nossodireito\scripts\validate_all.py
}
Set-Alias nva Validate-All-NossoDireito

# Função para análise 360
function Analise360-NossoDireito {
    $env:PYTHONIOENCODING='utf-8'
    python C:\path\to\nossodireito\scripts\analise360.py
}
Set-Alias n360 Analise360-NossoDireito
```

**Uso depois:**
```powershell
nv      # Master compliance
nva     # Validate all
n360    # Análise 360
```

---

## 🎓 BOAS PRÁTICAS

### ✅ DO (Recomendado)

1. **Rodar master_compliance.py antes de commitar**
   - Garante qualidade constante
   - Detecta problemas cedo

2. **Fazer backup antes de modificar direitos.json**
   ```bash
   cp data/direitos.json data/direitos.json.backup
   ```

3. **Revisar conteúdo gerado por complete_beneficios.py**
   - Templates são genéricos
   - Customizar para cada benefício

4. **Monitorar cobertura semanalmente**
   ```bash
   python scripts/analise360.py
   ```

5. **Usar --fix com cuidado**
   - Verificar backup existe
   - Testar em ambiente dev primeiro

---

### ❌ DON'T (Evitar)

1. **Não commitar se score < 95%**
   - Resolver problemas antes
   - Manter qualidade alta

2. **Não editar manualmente benefícios sem critérios**
   - Usar `analise360.py` como guia
   - Seguir 7 critérios de qualidade

3. **Não ignorar timeouts em validate_sources.py**
   - Pode indicar URLs quebrados
   - Verificar conectividade

4. **Não rodar --fix em produção sem backup**
   - Sempre ter backup recente
   - Testar mudanças antes

5. **Não confiar 100% em templates automáticos**
   - Revisar tudo manualmente
   - Customizar para contexto específico

---

## 🆘 SUPORTE

### Problemas comuns já resolvidos:

1. ✅ UTF-8 encoding (emojis) → `PYTHONIOENCODING='utf-8'`
2. ✅ ANÁLISE 360 não captura → `if __name__ == '__main__':` adicionado
3. ✅ SRI gov.br → Exceção para domínios .gov.br (crossorigin only)
4. ✅ Timeout validate_sources → Esperado (muitas URLs)

### Novos problemas:

1. Abrir issue no GitHub
2. Ou consultar documentação em `docs/`
3. Ou debugar com verbose:
   ```bash
   python -v script.py
   ```

---

## 📈 MÉTRICAS DE SUCESSO

### Curto Prazo (Semanal)
- ✅ Master compliance: 100%
- ✅ Análise 360: Cobertura ≥75%, Completude ≥20
- ✅ Zero commits com score < 95%

### Médio Prazo (Mensal)
- ✅ Automação: ≥60% (implementar P0-P1)
- ✅ Testes unitários: ≥80% coverage
- ✅ Backup: Automático diário

### Longo Prazo (Trimestral)
- ✅ Automação: ≥80% (implementar P0-P3)
- ✅ Dashboard: Métricas históricas
- ✅ CI/CD: GitHub Actions em produção

---

**🎉 Você está pronto para usar todas as validações!**

Comandos principais:
1. `python scripts/validate_all.py` → Tudo de uma vez
2. `python scripts/master_compliance.py` → Validação principal
3. `python scripts/analise360.py` → Análise de conteúdo
4. `python scripts/complete_beneficios.py` → Auto-completar

---

*Guia atualizado em: 2026-02-12*
*NossoDireito — 100% Compliance*
