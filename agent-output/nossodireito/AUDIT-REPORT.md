# AUDIT REPORT — NossoDireito v1.21.1 → v1.22.0

**Data**: 2026-05-19
**Baseline tag**: `pre-audit-v1.21.1` (rollback: `git reset --hard pre-audit-v1.21.1`)
**Escopo**: estrutura, validadores fantasmas, código morto, duplicação, LGPD, Azure CAF/WAF
**Severidades**: 🔴 CRITICAL · 🟠 HIGH · 🟡 MEDIUM · 🟢 LOW

---

## SUMÁRIO EXECUTIVO

| Categoria | Achados | Maior risco |
|---|---|---|
| Validadores fantasmas | 4 | 🔴 Score 100% mascarando warnings reais |
| Bloat de scripts | 9002 linhas / 24 .py | 🟠 `master_compliance.py` 2772 linhas |
| Duplicação | 3 grupos | 🟡 `SECURITY.md` vs `SECURITY_AUDIT.md`; 3 classes `ValidationResult`/`MasterValidator` em arquivos diferentes |
| Bloat de bump_version | 13 alvos | 🟡 8 dos 13 não precisam de stamp |
| Cruft local (não commitado) | 11 arquivos | 🟢 `.DS_Store`, 3× `terraform.tfstate*`, 6× `tfplan*` |
| LGPD compliance | 1 gap | 🟠 `index.html` sem seção "Direitos do Titular" (Art. 18) |
| Azure CAF/WAF | 2 gaps | 🟡 Actions sem pin (tflint, checkov) |
| Histórico git | OK | gitleaks: **0 segredos** em 258 commits |

**Já corrigido nesta auditoria (PR #95)**: gitleaks + scan_pii.py no pre-commit (LGPD Art. 46-49).

---

## 1. VALIDADORES FANTASMAS 🔴

### 1.1 Score 100% inflacionado
`master_compliance.py` reporta **1107.2/1107.2 = 100.00%** enquanto exibe 8+ warnings na mesma execução:

```
⚠️  [DEAD_CODE] Python: 7 importações não usadas
⚠️  [ORFAOS] 7 problema(s) de higiene detectado(s)
⚠️  [PERFORMANCE] index.html: 103KB (> 100KB)
⚠️  [PERFORMANCE] js/app.js: 169KB (> 110KB)
⚠️  [CLOUD_SECURITY] LGPD Runtime: index.html sem seção Direitos do Titular
⚠️  [CICD] Action sem pin: terraform-linters/setup-tflint@v4
⚠️  [CICD] Action sem pin: bridgecrewio/checkov-action@v12
⚠️  [LOGICA] 5 categoria(s) sem documentos
```

**Causa**: Warnings (`type: 'WARN'`) **não decrementam pontuação**, só ERRORS. Resultado: 100% mente.
**Correção**: cada WARN deve subtrair fração (ex: 0.5pt). Sem isso, validator dá falso senso de OK.

### 1.2 Desincronização validator vs README
Validator reporta `1107.2/1107.2`, README diz `1126.2/1126.2`. **Update automático falhou de novo** entre PR #94 e agora — provavelmente porque categorias foram adicionadas/removidas sem rodar `update_readme_badge()`. Mesma classe de bug que o PR #94 tentou resolver.

### 1.3 Checks de existência ≠ checks de funcionamento
```
✅ [ARQUITETURA] scripts/validate_sources.py presente
```
21 categorias × N checks só validam **existência** ou **sintaxe**, não comportamento. Ex: `validate_content.py: sintaxe válida` não diz se o conteúdo está válido — só que o `.py` compila.

### 1.4 Scripts referenciados que não validam nada
- `check_sources_freshness.py`: roda no pre-commit mas com `|| true` (nunca bloqueia). Existência sem efeito.
- `audit_automation.py`: 334 linhas; só 4 refs externas — investigar se ainda é executado por CI.

---

## 2. BLOAT 🟠

### 2.1 Scripts
| Arquivo | Linhas | Recomendação |
|---|---|---|
| `master_compliance.py` | **2772** | Refatorar em módulos (`validators/data.py`, `validators/security.py`, ...). Reduzir ≥40%. |
| `discover_benefits.py` | 1428 | Verificar se ainda é usado (one-shot script?). |
| `validate_sources.py` | 830 | Sobreposição com `validate_urls.py` (294 linhas). Mesclar. |
| `validate_all.py` | 722 | Sobreposição com `master_compliance.py`. Aposentar (já que master existe). |

**Total**: 9002 linhas em 24 scripts. Após consolidação razoável: ~4000 linhas em 12 scripts.

### 2.2 bump_version.py — 13 alvos, 5 essenciais

| Alvo | Realmente precisa de stamp? |
|---|---|
| `package.json` | ✅ npm version |
| `manifest.json` | ✅ PWA version |
| `sw.js` (`CACHE_VERSION`) | ✅ cache invalidation |
| `index.html` (meta version) | ✅ build identifier |
| `CHANGELOG.md` | ✅ histórico |
| `data/direitos.json` | ⚠️ dado vs metadado |
| `data/dicionario_pcd.json` | ⚠️ dado vs metadado |
| `README.md` | 🟡 só badge |
| `GOVERNANCE.md` | ❌ sem necessidade |
| `SECURITY_AUDIT.md` | ❌ sem necessidade |
| `docs/SECURITY-LGPD.md` | ❌ sem necessidade |
| `docs/ARCHITECTURE.md` | ❌ sem necessidade |
| `docs/OPERATIONS.md` | ❌ sem necessidade |
| `docs/REPLICATION.md` | ❌ sem necessidade |
| `scripts/master_compliance.py` | ❌ sem necessidade |
| `scripts/validate_content.py` | ❌ sem necessidade |
| `tests/test_comprehensive.py` | ❌ sem necessidade |

**Recomendação**: reduzir para **5 alvos** + 1 helper que injeta `__VERSION__` via build-time onde for útil.

### 2.3 CHANGELOG.md
1751 linhas / 45 versões. Acima de 1000 linhas, considerar arquivar versões >12 meses em `CHANGELOG.archive.md`.

---

## 3. DUPLICAÇÃO 🟡

| Grupo | Arquivos | Ação |
|---|---|---|
| Validation result/report classes | `validate_all.py::ValidationResult`, `validate_sources.py::ValidationResult` + `ValidationReport` | Extrair `scripts/_lib/validation.py` |
| URL validation | `validate_urls.py::extract_all_urls`, `validate_sources.py::extract_all_urls` | Mesma função em 2 arquivos. Unificar. |
| Security docs | `SECURITY.md` (91 linhas) + `SECURITY_AUDIT.md` (271 linhas) | Manter `SECURITY.md` como entrypoint; mover detalhes auditados para `docs/SECURITY-AUDIT.md` ou anexar |
| Requirements | `requirements.txt` + `requirements-dev.txt` | OK manter (padrão Python) |

---

## 4. CRUFT LOCAL (não commitado, mas polui dev) 🟢

Tudo já está gitignored. Apenas higiene de workspace:
```
.DS_Store, docs/.DS_Store
terraform/terraform.tfstate
terraform/terraform.tfstate.backup
terraform/terraform.tfstate.1779122074.backup
terraform/tfplan
terraform/tfplan-final
terraform/tfplan-final-check
terraform/tfplan-post-recovery
terraform/tfplan-private-final
terraform/tfplan-recover-kv-public
validation_legal_report.json
scripts/__pycache__/
```

**Comando seguro de limpeza**:
```bash
git clean -fdX -e 'node_modules' -e '.venv'   # remove tudo gitignored exceto deps
```

---

## 5. LGPD 🟠

### 5.1 Gap detectado pelo próprio validator
> `index.html` sem seção "Direitos do Titular" (LGPD Art. 18)

**Art. 18 LGPD**: o titular tem direito a: confirmação, acesso, correção, anonimização, portabilidade, eliminação, informação sobre compartilhamento, revogação de consentimento. **Precisa estar acessível no site**, não só em `docs/SECURITY-LGPD.md`.

### 5.2 Verificações OK (validator + scan manual)
- ✅ 0 segredos no histórico (258 commits)
- ✅ 0 PII no código (server.js só tem email DPO público — MEDIUM/aceitável)
- ✅ Managed Identity, HTTPS-only, Key Vault Soft Delete
- ✅ DPO email + canal de contato

### 5.3 Pré-commit hardening
PR #95 adiciona: gitleaks + `scan_pii.py` (CPF/RG/CNPJ/email/Bearer). Bloqueia commit em CRITICAL.

---

## 6. AZURE CAF/WAF 🟡

| Pilar | Gap | Ação |
|---|---|---|
| Operational Excellence | 2 actions sem pin SHA: `setup-tflint@v4`, `checkov-action@v12` | Pinar para SHA imutável |
| Reliability | tfstate local backups (3 arquivos) | Confirmar remote state habilitado |
| Security | OK — MSI, HTTPS, Key Vault, soft-delete | — |
| Cost | OK — `budget.tf` presente, B1 SKU adequado | — |
| Performance | `index.html` 103KB, `app.js` 169KB | Considerar minificação no build |

---

## 7. PLANO DE EXECUÇÃO (PRs próximos)

Cada PR ≤300 linhas, testável, reversível.

| # | Título | Risco | Status |
|---|---|---|---|
| **#95** | gitleaks + PII pre-commit | 🟢 zero | ✅ CRIADO |
| **#96** | Este audit report | 🟢 zero | em curso |
| #97 | Score: WARNs decrementam (fix fantasma 1.1) | 🟢 baixo | pendente |
| #98 | Slim `bump_version.py`: 13 → 5 alvos | 🟡 médio | pendente |
| #99 | Consolidar `validate_sources` + `validate_urls`; aposentar `validate_all.py` | 🟠 alto | pendente |
| #100 | LGPD: seção Direitos do Titular em `index.html` | 🟢 baixo | pendente |
| #101 | Pin SHAs em GitHub Actions | 🟢 baixo | pendente |
| #102 | Refactor `master_compliance.py` em módulos | 🔴 alto — requer revisão humana | bloqueado, precisa autorização explícita |

**Decisão pedida**: PR #102 (refactor de 2772 linhas) **não deve ser feito autonomamente** — o risco de quebrar 100% dos checks é real. Faça por categoria, um módulo por PR.

---

**Próximas ações automáticas (esta sessão)**: #97, #98, #100, #101.
**Bloqueado por revisão humana**: #99 (alto risco de quebrar testes), #102.
