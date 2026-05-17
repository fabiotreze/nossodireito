# REDEPLOY — Recriação do ambiente do zero

**Versão:** 1.15.0
**Atualizado:** 2026-05-17

Este documento descreve como reconstruir o ambiente NossoDireito a partir do
zero em uma nova subscription Azure (ou para fins de Disaster Recovery).

Todo o código necessário está no repositório — não há dependências externas
fora dos serviços Azure provisionados via Terraform.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Verificar             |
| ---------- | ------------- | --------------------- |
| Azure CLI  | 2.60+         | `az --version`        |
| Terraform  | 1.6+          | `terraform --version` |
| Node.js    | 22 LTS        | `node --version`      |
| Python     | 3.11+         | `python3 --version`   |
| GitHub CLI | 2.40+         | `gh --version`        |

Acessos necessários:

- Subscription Azure com role **Owner** (criação de SP e atribuições RBAC)
- Conta GitHub com permissão de admin no fork do repositório

---

## Etapa 1 — Clonar o repositório

```bash
git clone https://github.com/fabiotreze/nossodireito.git
cd nossodireito
npm ci
pip install -r requirements.txt 2>/dev/null || true
```

---

## Etapa 2 — Bootstrap Azure (Service Principal + OIDC)

Cria o SP que o GitHub Actions usará para deploy via OIDC (sem secrets de
senha) e atribui as roles necessárias.

```bash
# 1. Login interativo
az login
az account set --subscription "<SUBSCRIPTION_ID>"

# 2. Criar SP com federated credential (OIDC)
SUB_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

az ad sp create-for-rbac \
  --name "sp-nossodireito-deploy" \
  --role "Contributor" \
  --scopes "/subscriptions/${SUB_ID}" \
  --json-auth > /tmp/sp.json

CLIENT_ID=$(jq -r .clientId /tmp/sp.json)

# 3. Federated credential para GitHub Actions (branch main)
az ad app federated-credential create \
  --id "${CLIENT_ID}" \
  --parameters "{
    \"name\": \"github-main\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:fabiotreze/nossodireito:ref:refs/heads/main\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

# 4. Limpar arquivo temporário com credenciais
shred -u /tmp/sp.json
```

---

## Etapa 3 — Configurar GitHub Secrets

```bash
gh secret set ARM_CLIENT_ID       --body "${CLIENT_ID}"
gh secret set ARM_TENANT_ID       --body "${TENANT_ID}"
gh secret set ARM_SUBSCRIPTION_ID --body "${SUB_ID}"
```

(Se usar certificado SSL próprio: `gh secret set TF_VAR_pfx_password`.)

---

## Etapa 4 — Configurar variáveis Terraform

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Editar terraform/terraform.tfvars: preencher subscription_id, alert_email, etc.
```

> ⚠️ `terraform.tfvars` está no `.gitignore` — nunca será commitado.

---

## Etapa 5 — Deploy infraestrutura

```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Recursos provisionados (região `brazilsouth`):

- Resource Group `rg-nossodireito-br`
- App Service Plan `asp-nossodireito-br` (B1)
- App Service `app-nossodireito-br` (Node 22 LTS)
- Application Insights `ai-nossodireito-br`
- Storage Account (estado App Insights)
- Container Registry (futuras imagens Docker)
- Key Vault `kv-nossodireito-br` (opcional, se SSL próprio habilitado)
- **POC IA opt-in:** Cognitive Services `cog-nossodireito-br` (F0, Document
  Intelligence) — desligado por default via `AI_ANALYSIS_ENABLED=false`.

### DNS — domínio customizado (Cloudflare)

O domínio `fabiotreze.com` é gerenciado no **Cloudflare DNS** (não no
registrar). Para apontar `nossodireito.fabiotreze.com` ao App Service:

1. Após `terraform apply` (primeira passada, sem `enable_custom_domain`),
   copie o `default_hostname` (ex: `app-nossodireito-br.azurewebsites.net`).
2. No painel Cloudflare → DNS → adicionar registro:
   - **Type:** `CNAME`
   - **Name:** `nossodireito`
   - **Target:** `app-nossodireito-br.azurewebsites.net`
   - **Proxy status:** `DNS only` (☁ cinza) — necessário para validação
     do domínio no Azure. Pode ativar proxy (☁ laranja) depois.
   - **TTL:** Auto
3. Verificar propagação: `dig nossodireito.fabiotreze.com CNAME +short`
4. Habilitar `enable_custom_domain = true` em `terraform.tfvars` e rodar
   `terraform apply` novamente.

> Se ativar proxy Cloudflare (laranja) depois, configurar SSL mode como
> **Full (strict)** para evitar redirect loop com o HTTPS do App Service.

---

## Etapa 6 — Deploy da aplicação

Após `terraform apply` concluir, faça push para `main` — o workflow
`deploy.yml` rodará automaticamente. Para deploy manual:

```bash
cd ..
zip -r deploy.zip . \
  -x "node_modules/*" -x ".git/*" -x "terraform/*" \
  -x ".github/*" -x "scripts/*" -x "tests/*" -x "docs/*"
az webapp deploy \
  --resource-group rg-nossodireito-br \
  --name app-nossodireito-br \
  --src-path deploy.zip --type zip
rm deploy.zip
```

---

## Etapa 7 — Validar deploy

```bash
HOST=$(az webapp show -g rg-nossodireito-br -n app-nossodireito-br \
  --query defaultHostName -o tsv)
curl -sI "https://${HOST}/api/health" | head -5
```

Resposta esperada: `HTTP/2 200`.

---

## Disaster Recovery — Tempo estimado

| Fase                      | Tempo       |
| ------------------------- | ----------- |
| Etapa 1 (clone + deps)    | ~3 min      |
| Etapa 2 (SP + OIDC)       | ~5 min      |
| Etapa 3 (secrets)         | ~1 min      |
| Etapa 4 (tfvars)          | ~2 min      |
| Etapa 5 (terraform apply) | ~10 min     |
| Etapa 6 (app deploy)      | ~5 min      |
| **Total RTO**             | **~26 min** |

---

## Dados persistidos — O que NÃO está no Git

| Dado                                        | Onde fica                                 | Backup                 |
| ------------------------------------------- | ----------------------------------------- | ---------------------- |
| Estado Terraform (`*.tfstate`)              | Local (futuro: backend remoto em Storage) | Manual ou via backend  |
| Certificado PFX (`fabiotreze-wildcard.pfx`) | Key Vault Azure                           | Export do Key Vault    |
| Senha PFX                                   | GitHub Secret `TF_VAR_pfx_password`       | Vault pessoal do owner |
| Dados de usuário                            | **Nenhum — LGPD zero collection**         | N/A                    |

> A aplicação não coleta dados pessoais. Toda persistência é client-side
> (IndexedDB + Web Crypto API). Não há backup de dados de usuário porque
> não existem dados de usuário no servidor.

---

## Migração de tenant Azure

Se for migrar para outra subscription/tenant (como em 2026-03), repita
Etapas 2-5 no novo tenant. Não há dados a migrar do tenant antigo — apenas
infraestrutura. Para preservar histórico de App Insights, exporte queries
via portal antes de destruir o ambiente antigo.

---

## Referências

- `terraform/` — todo o IaC (variáveis em `variables.tf`, recursos em
  `main.tf` + `ai-doc-intelligence.tf`)
- `docs/ARCHITECTURE.md` — diagrama lógico
- `SECURITY_AUDIT.md` — 14 vetores de segurança documentados
- `.github/workflows/terraform.yml` — pipeline CI/CD do IaC
- `.github/workflows/deploy.yml` — pipeline de deploy da aplicação
