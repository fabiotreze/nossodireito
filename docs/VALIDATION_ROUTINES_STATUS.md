# 🔄 ROTINAS DE VALIDAÇÃO AUTOMÁTICA — STATUS & ROADMAP

**Projeto:** NossoDireito
**Versão:** 1.10.0
**Data:** 2026-02-12
**Status Atual:** ✅ 100% Compliance | ⚠️ ~40% Automação

---

## 📋 ÍNDICE

1. [O QUE EXISTE HOJE](#o-que-existe-hoje)
2. [O QUE NÃO EXISTE (GAPS)](#o-que-não-existe-gaps)
3. [ROTINA GERAL IDEAL](#rotina-geral-ideal)
4. [ROADMAP DE IMPLEMENTAÇÃO](#roadmap-de-implementação)
5. [BOAS PRÁTICAS ATUAIS](#boas-práticas-atuais)

---

## 🟢 O QUE EXISTE HOJE

### 1. Master Compliance Validator (scripts/master_compliance.py)

**Execução:** Manual (`python scripts/master_compliance.py`)
**Frequência:** Ad-hoc (quando desenvolvedor roda)
**Tempo:** ~1.5s

#### Validações Implementadas:

| # | Categoria | O que valida | Automático? |
|---|-----------|--------------|-------------|
| 1 | DADOS | ✅ Schema JSON, estrutura, categorias | ✅ Sim |
| 2 | CÓDIGO | ✅ HTML/CSS/JS: sintaxe, estrutura | ✅ Sim |
| 3 | FONTES | ✅ URLs .gov.br: conectividade HTTP | ⚠️ Parcial |
| 4 | ARQUITETURA | ✅ Estrutura de pastas, organização | ✅ Sim |
| 5 | DOCUMENTAÇÃO | ✅ README, LICENSE, docs/ | ✅ Sim |
| 6 | SEGURANÇA | ✅ HTTPS, CSP, SRI | ✅ Sim |
| 7 | PERFORMANCE | ✅ Métricas, carregamento | ✅ Sim |
| 8 | ACESSIBILIDADE | ✅ WCAG 2.1, VLibras | ✅ Sim |
| 9 | SEO | ✅ Meta tags, sitemap, robots | ✅ Sim |
| 10 | INFRAESTRUTURA | ✅ PWA, manifest, sw.js | ✅ Sim |
| 11 | TESTES | ✅ E2E presence check | ⚠️ Parcial |
| 12 | DEAD CODE | ✅ Detecção de código inutilizado | ✅ Sim |
| 13 | ÓRFÃOS | ✅ Arquivos não referenciados | ✅ Sim |
| 14 | LÓGICA | ✅ Validação de fluxos | ✅ Sim |
| 15 | REGULATORY | ✅ LGPD, termos de uso | ✅ Sim |
| 16 | CLOUD_SECURITY | ✅ Best practices cloud | ✅ Sim |
| 17 | CI/CD | ✅ Git structure, .gitignore | ⚠️ Parcial |
| 18 | DEPENDÊNCIAS | ✅ requirements.txt, SRI | ✅ Sim |
| 19 | CHANGELOG | ✅ Semver, Keep a Changelog | ✅ Sim |
| 20 | ANÁLISE 360 | ✅ Cobertura, completude, IPVA | ✅ Sim |

**Cobertura:** 20 categorias, 973.9 pontos
**Limitações:**
- ❌ Não roda automaticamente (requer execução manual)
- ❌ Não tem notificações de falha
- ❌ Não mantém histórico de runs
- ❌ Não valida **conteúdo semântico** (só estrutura)

---

### 2. Validação de Fontes (scripts/validate_sources.py)

**Execução:** Manual
**Frequência:** Ad-hoc
**Tempo:** ~30s

#### O que faz:
- ✅ Verifica conectividade de URLs .gov.br
- ✅ Valida HTTP status code (200 OK)
- ✅ Checa formato JSON de links

#### Limitações:
- ❌ **NÃO** valida conteúdo das páginas
- ❌ **NÃO** detecta mudanças de legislação
- ❌ **NÃO** verifica se benefício ainda existe
- ❌ **NÃO** valida formato de números de leis

---

### 3. Análise 360° (scripts/analise360.py)

**Execução:** Manual ou via master_compliance
**Frequência:** Ad-hoc
**Tempo:** <1s

#### O que faz:
- ✅ Calcula cobertura de benefícios implementados
- ✅ Identifica benefícios completos vs parciais
- ✅ Valida IPVA estadual (27/27 estados)
- ✅ Gera diagnóstico de gaps automaticamente

#### Critérios de Qualidade (7 requisitos):
1. ≥5 requisitos
2. ≥4 documentos
3. ≥6 passos
4. ≥4 dicas
5. ≥2 links
6. ≥1 base_legal
7. valor não vazio

#### Limitações:
- ❌ **NÃO** valida correção dos dados (só presença)
- ❌ **NÃO** verifica atualidade de informações
- ❌ **NÃO** compara com fontes oficiais

---

### 4. Complete Benefícios (scripts/complete_beneficios.py)

**Execução:** Manual
**Frequência:** Ad-hoc
**Tempo:** <5s

#### O que faz:
- ✅ Preenche campos faltantes automaticamente
- ✅ Cria backup antes de modificar
- ✅ Usa templates contextualizados

#### Limitações:
- ❌ Templates genéricos (não específicos)
- ❌ Não usa IA para sugestões inteligentes
- ❌ Não valida qualidade do conteúdo preenchido

---

### 5. Auditoria de Automação (scripts/audit_automation.py)

**Execução:** Manual
**Frequência:** Ad-hoc
**Tempo:** <1s

#### O que faz:
- ✅ Mapeia gaps de automação
- ✅ Prioriza recomendações por impacto
- ✅ Estima esforço de implementação
- ✅ Gera relatório em Markdown

#### Limitações:
- ❌ Só gera relatórios estáticos
- ❌ Não executa correções automaticamente

---

## 🔴 O QUE NÃO EXISTE (GAPS)

### ❌ 1. Rotina Geral de Revalidação Automática

**Status:** NÃO EXISTE
**Impacto:** ALTO
**Prioridade:** P0

#### O que falta:
- Cron job / GitHub Action para rodar diariamente
- Execução automática de **todos os scripts** em sequência
- Detecção automática de falhas
- Notificações (email/Slack) em caso de problemas
- Dashboard de status em tempo real

#### Como seria:
```bash
# Cron diário (00:00 UTC)
0 0 * * * /usr/bin/python3 /path/scripts/validate_all.py --notify

# validate_all.py executaria:
1. master_compliance.py    → Score geral
2. validate_sources.py     → URLs .gov.br
3. analise360.py           → Cobertura/completude
4. audit_automation.py     → Gaps de automação
5. validate_legal.py       → Base legal (NOVO)
6. validate_content.py     → Conteúdo semântico (NOVO)
7. validate_ipva_states.py → IPVA atualizado (NOVO)
```

---

### ❌ 2. Validação de Conteúdo Semântico

**Status:** NÃO EXISTE
**Impacto:** ALTO
**Prioridade:** P1

#### Gaps críticos:
- ❌ Verificação de correção gramatical
- ❌ Detecção de informações desatualizadas
- ❌ Validação de valores monetários
- ❌ Conferência de datas (ex: "atualizado em 2023" em 2026)
- ❌ Consistência entre seções

#### Como implementar:
```python
# scripts/validate_content.py
def validate_semantic_content():
    # 1. Verificar gramática (LanguageTool API)
    # 2. Detectar datas antigas (regex + comparação)
    # 3. Validar valores monetários (scraped vs stored)
    # 4. Verificar consistência interna
    # 5. Detectar links quebrados internos
    pass
```

---

### ❌ 3. Validação de Base Legal

**Status:** NÃO EXISTE
**Impacto:** CRÍTICO ⚠️
**Prioridade:** P0

#### Gaps críticos:
- ❌ Scraping de legislação em sites oficiais
- ❌ Detecção de leis revogadas/alteradas
- ❌ Validação de formato de números de leis
- ❌ Verificação de vigência de normas
- ❌ Comparação de direitos.json vs legislação atual

#### Como implementar:
```python
# scripts/validate_legal_compliance.py
def validate_legal_base():
    # 1. Scrape planalto.gov.br
    # 2. Verificar vigência de cada lei citada
    # 3. Comparar artigos citados vs texto oficial
    # 4. Alertar sobre revogações
    # 5. Sugerir atualizações
    pass
```

**Fontes de dados:**
- planalto.gov.br/ccivil_03/leis
- legis.senado.leg.br
- www4.planalto.gov.br/legislacao

---

### ❌ 4. Testes Unitários

**Status:** NÃO EXISTE
**Impacto:** ALTO
**Prioridade:** P1

#### O que falta:
- ❌ `tests/test_master_compliance.py`
- ❌ `tests/test_analise360.py`
- ❌ `tests/test_validate_sources.py`
- ❌ `tests/test_complete_beneficios.py`
- ❌ Coverage report (pytest-cov)
- ❌ CI/CD integration (GitHub Actions)

#### Template:
```python
# tests/test_analise360.py
import pytest
from scripts.analise360 import is_beneficio_completo

def test_beneficio_completo_valido():
    cat = {
        'requisitos': ['a', 'b', 'c', 'd', 'e'],
        'documentos': ['1', '2', '3', '4'],
        'passo_a_passo': ['1', '2', '3', '4', '5', '6'],
        'dicas': ['a', 'b', 'c', 'd'],
        'links': [{'url': 'x'}, {'url': 'y'}],
        'base_legal': ['Lei 1'],
        'valor': 'Isento ou valor variável'
    }
    assert is_beneficio_completo(cat) == True

def test_beneficio_parcial():
    cat = {'requisitos': ['a', 'b']}  # Faltam campos
    assert is_beneficio_completo(cat) == False
```

---

### ❌ 5. Backup Automático

**Status:** NÃO EXISTE (só manual via complete_beneficios.py)
**Impacto:** ALTO ⚠️
**Prioridade:** P0

#### O que falta:
- ❌ Backup diário automático
- ❌ Versionamento com timestamp
- ❌ Limpeza de backups antigos (>30 dias)
- ❌ Commit automático no Git
- ❌ Sincronização com cloud storage

#### Como implementar:
```python
# scripts/auto_backup.py
import shutil
import datetime
from pathlib import Path

def backup_daily():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Backup direitos.json
    shutil.copy(
        'data/direitos.json',
        f'backups/direitos_{timestamp}.json'
    )

    # Commit no Git
    os.system('git add backups/')
    os.system(f'git commit -m "Auto-backup {timestamp}"')

    # Limpar backups antigos
    cleanup_old_backups(days=30)
```

**Cron job:**
```bash
# Backup diário às 23:00
0 23 * * * /usr/bin/python3 /path/scripts/auto_backup.py
```

---

### ❌ 6. Monitoramento Contínuo

**Status:** NÃO EXISTE
**Impacto:** MÉDIO
**Prioridade:** P2

#### O que falta:
- ❌ Dashboard de qualidade em tempo real
- ❌ Histórico de métricas (score ao longo do tempo)
- ❌ Alertas de regressões
- ❌ Badge no README (shields.io)
- ❌ Exportação de relatórios PDF

#### Como implementar:
```yaml
# .github/workflows/quality_monitor.yml
name: Quality Monitor

on:
  schedule:
    - cron: '0 0 * * *'  # Diário às 00:00 UTC
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Master Compliance
        run: python scripts/master_compliance.py
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: compliance-report
          path: compliance_report.txt
      - name: Send Slack Notification
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {"text": "❌ NossoDireito compliance failed!"}
```

---

### ❌ 7. JSON Schema Formal

**Status:** NÃO EXISTE
**Impacto:** MÉDIO
**Prioridade:** P1

#### O que falta:
- ❌ `schemas/direitos.schema.json` (JSON Schema Draft-07)
- ❌ Validação automática no master_compliance
- ❌ Documentação de todos os campos
- ❌ Exemplos de uso

#### Template:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Direitos PcD",
  "type": "object",
  "required": ["categorias"],
  "properties": {
    "categorias": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "titulo", "descricao"],
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^[a-z_]+$"
          },
          "titulo": {
            "type": "string",
            "minLength": 5
          },
          "requisitos": {
            "type": "array",
            "minItems": 5,
            "items": {"type": "string"}
          }
        }
      }
    }
  }
}
```

**Validação:**
```python
import jsonschema

with open('schemas/direitos.schema.json') as f:
    schema = json.load(f)

with open('data/direitos.json') as f:
    data = json.load(f)

jsonschema.validate(instance=data, schema=schema)
```

---

## 🎯 ROTINA GERAL IDEAL

### validate_all.py (Script Master)

```python
#!/usr/bin/env python3
"""
VALIDAÇÃO COMPLETA — Executa todas as validações em sequência
Uso: python scripts/validate_all.py [--notify] [--fix]
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

class MasterValidator:
    def __init__(self, notify=False, auto_fix=False):
        self.notify = notify
        self.auto_fix = auto_fix
        self.results = []

    def run_all_validations(self):
        """Executa todas as validações em ordem de prioridade"""

        validations = [
            # 1. Estrutura & Dados
            ('master_compliance', 'python scripts/master_compliance.py'),

            # 2. Conteúdo & Qualidade
            ('analise360', 'python scripts/analise360.py'),
            ('validate_content', 'python scripts/validate_content.py'),  # NOVO

            # 3. Fontes & Legal
            ('validate_sources', 'python scripts/validate_sources.py'),
            ('validate_legal', 'python scripts/validate_legal_compliance.py'),  # NOVO

            # 4. IPVA & Estados
            ('validate_ipva', 'python scripts/validate_ipva_states.py'),  # NOVO

            # 5. Auto-correção (se --fix)
            ('complete_beneficios', 'python scripts/complete_beneficios.py') if self.auto_fix else None,

            # 6. Auditoria de Automação
            ('audit_automation', 'python scripts/audit_automation.py'),

            # 7. Backup
            ('backup', 'python scripts/auto_backup.py'),
        ]

        print("=" * 100)
        print("🔄 VALIDAÇÃO COMPLETA — NOSSODIREITO")
        print("=" * 100)
        print(f"Hora: {datetime.now()}")
        print(f"Modo: {'AUTO-FIX' if self.auto_fix else 'READ-ONLY'}")
        print()

        for name, cmd in validations:
            if cmd is None:
                continue

            print(f"▶️  Executando: {name}...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            self.results.append({
                'name': name,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            })

            if result.returncode == 0:
                print(f"   ✅ {name}: OK")
            else:
                print(f"   ❌ {name}: FAILED")
                print(f"      Error: {result.stderr[:200]}")

        print()
        print("=" * 100)

        # Gerar relatório
        self.generate_report()

        # Notificar se necessário
        if self.notify:
            self.send_notifications()

    def generate_report(self):
        """Gera relatório consolidado"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['returncode'] == 0)
        failed = total - passed

        print(f"📊 RESUMO: {passed}/{total} validações OK ({passed/total*100:.1f}%)")
        print()

        if failed > 0:
            print("❌ FALHAS:")
            for r in self.results:
                if r['returncode'] != 0:
                    print(f"   • {r['name']}")
            print()

        # Salvar em JSON
        with open('validation_report.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total': total,
                'passed': passed,
                'failed': failed,
                'results': self.results
            }, f, indent=2)

        print("📄 Relatório salvo em: validation_report.json")

    def send_notifications(self):
        """Envia notificações (email/Slack)"""
        failed = [r for r in self.results if r['returncode'] != 0]

        if failed:
            # Exemplo: enviar via Slack
            import requests
            webhook_url = os.getenv('SLACK_WEBHOOK_URL')
            if webhook_url:
                requests.post(webhook_url, json={
                    'text': f"❌ NossoDireito: {len(failed)} validações falharam!"
                })


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--notify', action='store_true', help='Enviar notificações')
    parser.add_argument('--fix', action='store_true', help='Auto-corrigir problemas')
    args = parser.parse_args()

    validator = MasterValidator(notify=args.notify, auto_fix=args.fix)
    validator.run_all_validations()


if __name__ == '__main__':
    main()
```

---

## 📅 ROADMAP DE IMPLEMENTAÇÃO

### Fase 1 — Fundação (Semana 1-2)

**Prioridade:** P0 (Crítico)
**Esforço:** 12 horas

1. ✅ **Backup Automático** (4h)
   - `scripts/auto_backup.py`
   - Cron job diário
   - Limpeza de backups antigos

2. ✅ **Validação de Base Legal** (8h)
   - `scripts/validate_legal_compliance.py`
   - Scraping de planalto.gov.br
   - Detecção de leis revogadas

---

### Fase 2 — Qualidade (Semana 3-4)

**Prioridade:** P1 (Alto)
**Esforço:** 22 horas

3. ✅ **JSON Schema** (6h)
   - `schemas/direitos.schema.json`
   - Validação automática

4. ✅ **Testes Unitários** (16h)
   - `tests/test_*.py`
   - Pytest + coverage
   - GitHub Actions CI

---

### Fase 3 — Monitoramento (Mês 2)

**Prioridade:** P2 (Médio)
**Esforço:** 22 horas

5. ✅ **Monitoramento Contínuo** (12h)
   - GitHub Actions diárias
   - Notificações Slack
   - Badge no README

6. ✅ **Auto-Preenchimento Inteligente** (10h)
   - IA para sugestões (GPT-4/Claude)
   - Modo interativo

---

### Fase 4 — Avançado (Mês 3-6)

**Prioridade:** P3 (Baixo)
**Esforço:** 44 horas

7. ✅ **Dashboard de Métricas** (20h)
   - Gráficos históricos
   - Exportação PDF

8. ✅ **Scraping gov.br** (24h)
   - Detecção de novos benefícios
   - Alertas de mudanças

---

## ✅ BOAS PRÁTICAS ATUAIS

### O que já fazemos bem:

1. **Versionamento Semântico**
   - ✅ CHANGELOG.md (Keep a Changelog)
   - ✅ Tags Git (v1.0.0, v1.1.0, etc.)
   - ✅ 18 versões documentadas

2. **Documentação**
   - ✅ README.md completo
   - ✅ docs/ com 25+ documentos
   - ✅ Comentários inline em scripts

3. **Estrutura de Código**
   - ✅ Modularização (funções separadas)
   - ✅ Cross-platform (pathlib)
   - ✅ UTF-8 encoding configurado

4. **Segurança**
   - ✅ SRI para CDNs
   - ✅ CSP headers
   - ✅ HTTPS enforcement

5. **Validação Manual**
   - ✅ 20 categorias implementadas
   - ✅ 973.9 pontos de verificação
   - ✅ Relatórios detalhados

### O que precisa melhorar:

1. **Automação**
   - ❌ Nada roda automaticamente
   - ❌ Sem cron jobs
   - ❌ Sem GitHub Actions

2. **Testes**
   - ❌ Zero testes unitários
   - ❌ Sem coverage
   - ❌ Sem CI/CD

3. **Backup**
   - ❌ Só manual
   - ❌ Sem versionamento automático
   - ❌ Sem cloud sync

4. **Monitoramento**
   - ❌ Sem dashboard
   - ❌ Sem histórico de métricas
   - ❌ Sem alertas

---

## 🎯 CONCLUSÃO

### Status Atual: ⚠️ FUNCIONAL MAS MANUAL

- ✅ **Validações:** Excelente cobertura (20 categorias)
- ⚠️ **Automação:** Tudo é manual (~40% automatizado)
- ❌ **Testes:** Nenhum teste unitário
- ❌ **Backup:** Só manual
- ❌ **Monitoramento:** Nenhum

### Meta de Automação: 🎯 ≥80%

**Para chegar lá, implementar:**

1. **validate_all.py** — Rotina geral de revalidação
2. **GitHub Actions** — CI/CD automático
3. **Testes unitários** — pytest + coverage
4. **Backup automático** — Cron diário
5. **Validação de base legal** — Scraping legislação
6. **Monitoramento contínuo** — Dashboard + alertas

**Esforço total:** ~100 horas (2-3 meses com 1 dev part-time)

---

**Próximo passo imediato:** Implementar `validate_all.py` + backup automático (P0)

---

*Documento gerado em: 2026-02-12*
*NossoDireito — Master Compliance v1.10.0*
