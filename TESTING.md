# Como Testar o NossoDireito

Guia passo a passo para rodar todos os testes do projeto.

## O que você precisa ter instalado

| Ferramenta | Versão mínima | Como verificar |
|---|---|---|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Git | qualquer | `git --version` |

## Passo 1 — Clone o repositório

```bash
git clone https://github.com/fabiotreze/nossodireito.git
cd nossodireito
```

## Passo 2 — Crie o ambiente Python

```bash
python -m venv .venv
```

**Para ativar:**

- **Windows:** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

## Passo 3 — Instale as dependências

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Passo 4 — Rode os testes unitários

```bash
pytest tests/ -v
```

Resultado esperado: **710+ testes passando** (0 falhas).

## Passo 5 — Rode os testes E2E (navegador)

Os testes E2E abrem um navegador de verdade para testar o site.

**Instale o navegador de teste (só na primeira vez):**

```bash
playwright install chromium
```

**Rode os testes E2E:**

```bash
pytest tests/test_e2e_playwright.py -v
```

Resultado esperado: **74+ testes passando**.

> **Nota:** os testes E2E iniciam automaticamente um servidor local na porta 9876.

## Passo 6 — Validação de conteúdo

```bash
python scripts/validate_content.py
```

Resultado esperado: **0 erros**, apenas avisos (⚠️) sobre capitalização de siglas.

## Passo 7 — Master Compliance (auditoria completa)

```bash
python scripts/master_compliance.py
```

Resultado esperado: **100.00%** (nota máxima).

## Testar o site localmente

```bash
node server.js
```

Abra no navegador: **http://localhost:8080**

## Resumo rápido (copiar e colar)

```bash
git clone https://github.com/fabiotreze/nossodireito.git
cd nossodireito
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt -r requirements-dev.txt
playwright install chromium
pytest tests/ -v                # Testes unitários
pytest tests/test_e2e_playwright.py -v  # Testes E2E
python scripts/validate_content.py      # Validação de conteúdo
python scripts/master_compliance.py     # Auditoria completa
```

## Problemas comuns

| Problema | Solução |
|---|---|
| `ModuleNotFoundError: No module named 'pytest'` | Rode `pip install -r requirements-dev.txt` |
| `playwright install` falha | Verifique conexão com a internet |
| Testes E2E falham com "porta em uso" | Feche outros servidores na porta 9876 |
| `python` não encontrado | Use `python3` (Mac/Linux) |
| Node.js não encontrado | Instale em https://nodejs.org |

## Estrutura dos testes

```
tests/
├── test_analysis_scripts.py     # Scripts de análise
├── test_complete_validation.py  # Validação completa dos dados
├── test_e2e_automated.py        # E2E automatizado (pytest)
├── test_e2e_playwright.py       # E2E com navegador real
└── test_cross_browser.py        # Compatibilidade cross-browser

scripts/
├── validate_content.py          # Validação de conteúdo JSON
├── master_compliance.py         # Auditoria de conformidade
├── validate_all.py              # Validação geral
└── validate_govbr_urls.py       # Verificação de URLs gov.br
```
