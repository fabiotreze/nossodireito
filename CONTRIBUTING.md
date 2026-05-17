# Contribuindo para o NossoDireito

Obrigado por considerar contribuir! Este guia descreve o fluxo de trabalho
obrigatório para enviar mudanças ao repositório.

## Antes de começar

- Leia o [`README.md`](README.md) para entender o produto e como rodar
  localmente.
- Leia o [`SECURITY.md`](SECURITY.md) para reportar vulnerabilidades de
  forma responsável (não abra issue pública).
- Leia o [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md) para entender os
  gates obrigatórios de CI (versão, LGPD, telemetria anônima).
- Consulte o diagrama de arquitetura:
  [`docs/ARCHITECTURE.drawio`](docs/ARCHITECTURE.drawio) (abra no
  [draw.io desktop](https://github.com/jgraph/drawio-desktop) ou em
  <https://app.diagrams.net>).

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

Mudanças no produto (não em docs/CI) exigem bump de versão. Use o script:

```bash
python3 scripts/bump_version.py 1.16.1
```

Isso propaga a versão para todos os arquivos rastreados (HTML, manifest,
service worker, package.json etc). O gate `master_compliance.py` falha o
CI se as versões não estiverem alinhadas.

## CI obrigatório (status checks)

Os seguintes checks devem passar antes de fazer merge em `main`:

| Check          | O que valida                                            |
| -------------- | ------------------------------------------------------- |
| **Quality Gate** | `master_compliance.py`: versão, LGPD, telemetria, SRI |
| **CodeQL**       | Análise estática de segurança (SAST)                  |
| **gitleaks**     | Varredura por secrets vazados                         |

Além disso o repositório exige **linear history** (rebase ou squash, sem
merge commits) e bloqueia `force push`.

## Estrutura do projeto

- `index.html` — SPA single-file (UI + lógica de consulta)
- `js/` — módulos JavaScript (chamadas a Document Intelligence)
- `services/` — wrappers para Azure (Doc Intelligence, App Insights)
- `scripts/` — Python: compliance, bump de versão, deploy helpers
- `terraform/` — IaC do App Service + Application Insights
- `tests/` — testes Pytest (compliance, smoke)
- `docs/` — documentação técnica e diagrama de arquitetura
- `.github/workflows/` — pipelines de CI/CD (Quality Gate, deploy OIDC)

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
