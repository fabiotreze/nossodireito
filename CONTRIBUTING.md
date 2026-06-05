# Contribuindo para o NossoDireito (Guia Técnico)

Obrigado por considerar contribuir! Este guia descreve o fluxo de trabalho
obrigatório para enviar mudanças **de código** ao repositório. Para contribuir
com conteúdo (leis, links quebrados, informações desatualizadas), abra uma
[issue](https://github.com/fabiotreze/nossodireito/issues/new) descrevendo o
que precisa ser corrigido.

## Antes de começar

- Leia o [`README.md`](README.md) para entender o produto e como rodar
  localmente.
- Leia o [`SECURITY.md`](SECURITY.md) para reportar vulnerabilidades de
  forma responsável (não abra issue pública).
- Leia o [`GOVERNANCE.md`](GOVERNANCE.md) para entender os critérios de
  fontes oficiais, schema obrigatório de cada categoria e fluxo de revisão.
- Consulte os diagramas em [`docs/diagrams/`](docs/diagrams/) (abra os
  `.drawio` no [draw.io desktop](https://github.com/jgraph/drawio-desktop) ou em
  <https://app.diagrams.net>) e o [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Fluxo de Pull Request (mini-tutorial)

A branch `main` está protegida — não é possível fazer push direto.
Use sempre uma branch dedicada por mudança.

```bash
# 1. Sincronize com main
git checkout main && git pull

# 2. Crie uma branch (use prefixos: feat/, fix/, docs/, chore/, refactor/)
git checkout -b feat/minha-mudanca

# 3. Faça e commite as mudanças (Conventional Commits)
git add -A
git commit -m "feat: descreve a mudança em uma linha"

# 4. Envie a branch
git push -u origin feat/minha-mudanca

# 5. Abra o PR (preenche título/descrição a partir do commit)
gh pr create --fill

# 6. Aguarde os checks ficarem verdes (ver "CI obrigatório" abaixo)
gh pr checks --watch

# 7. Faça merge squash e apague a branch
gh pr merge --squash --delete-branch

# 8. Volte para main atualizada
git checkout main && git pull
```

## Convenção de commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

| Tipo       | Quando usar                                        |
| ---------- | -------------------------------------------------- |
| `feat`     | Nova funcionalidade visível ao usuário             |
| `fix`      | Correção de bug                                    |
| `docs`     | Mudanças apenas em documentação                    |
| `chore`    | Tarefas de manutenção (deps, configs, limpeza)     |
| `refactor` | Mudança de código sem alteração de comportamento   |
| `ci`       | Mudanças em workflows do GitHub Actions            |
| `test`     | Adição ou ajuste de testes                         |

Exemplos:

```text
feat: adiciona botão de copiar consulta gerada
fix: corrige scroll-padding para banner sticky duplo
docs: atualiza tutorial de contribuição
chore: bump version 1.16.0 → 1.16.1
```

## Versionamento

Mudanças no produto (não em docs/CI) exigem bump de versão em [`package.json`](package.json)
seguindo [SemVer](https://semver.org/lang/pt-BR/). Use Conventional Commit (`chore: bump version X.Y.Z`).
Mantenha `package.json` alinhado com as referências de cache-bust no `index.html`.

## CI obrigatório (status checks)

Os seguintes checks devem passar antes de fazer merge em `main`:

| Check          | O que valida                                                          |
| -------------- | --------------------------------------------------------------------- |
| **Quality Gate** | `scripts/validate_all.py --quick` (schema, conteúdo, base legal, etc.) |
| **CodeQL**       | Análise estática de segurança (Python + JavaScript/TypeScript)        |
| **gitleaks**     | Varredura por secrets vazados                                         |
| **Lighthouse**   | Performance / SEO / a11y / best-practices em `index.html`             |
| **A11y axe-core**| WCAG 2.1 AA em chromium / firefox / webkit                            |
| **Doc-link**     | `scripts/check_doc_links.mjs` — nenhum link relativo 404 em docs      |
| **Docs-truth**   | `scripts/check_docs_truth.mjs` — docs não citam features removidas    |

Além disso o repositório exige **linear history** (rebase ou squash, sem
merge commits) e bloqueia `force push`.

## Estrutura do projeto

- `index.html` — SPA single-file (UI + lógica de consulta)
- `js/` — módulos JavaScript (chamadas a Document Intelligence)
- `lib/` — módulos extraídos do `server.js` (MIME, security headers, file resolver, analytics, rate limit, Redis, AI analyze, gov.br proxy, infra handlers)
- `services/` — wrappers para Azure (Doc Intelligence)
- `scripts/` — Python: validate_all + validações de schema/conteúdo/fontes; JS: a11y_audit, check_doc_links, check_docs_truth
- `terraform/` — IaC do App Service + Key Vault + Redis + OpenAI + VNet
- `tests/` — testes Pytest + node:test
- `docs/` — documentação técnica e diagramas em `docs/diagrams/`
- `.github/workflows/` — pipelines de CI/CD (deploy, Quality Gate, CodeQL, gitleaks, Lighthouse, accessibility, link-check, terraform, dependabot-auto-merge)

## Reportando bugs e sugestões

- **Bug:** abra uma [issue](https://github.com/fabiotreze/nossodireito/issues/new)
  com passos para reproduzir, comportamento esperado e versão.
- **Sugestão de feature:** abra uma issue descrevendo o problema do
  usuário (não a solução).
- **Vulnerabilidade de segurança:** siga o processo em
  [`SECURITY.md`](SECURITY.md) — **não** abra issue pública.

## Código de conduta

Seja respeitoso. Comentários abusivos, discriminatórios ou em má-fé
levam a banimento imediato.
