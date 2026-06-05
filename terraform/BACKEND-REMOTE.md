# Backend remoto Terraform — guia operacional

## Estado atual

Desde **2026-05-31** o projeto opera com **backend remoto `azurerm` ATIVO**.
O state local em workstation e o artifact `terraform-state` no GitHub Actions
foram aposentados em favor do bloco abaixo, declarado em
[providers.tf](providers.tf):

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-nossodireito"
    storage_account_name = "stnossodireitobr"
    container_name       = "tfstate"
    key                  = "nossodireito.prod.tfstate"
    use_azuread_auth     = true
  }
}
```

Autenticação: **Azure AD** (sem chave de SA). State lock nativo via blob lease.

## Pré-requisitos por máquina

```bash
az login
az account set --subscription 3acb7300-a8c5-4354-9ad3-0a219a495b4a
cd terraform
terraform init
```

A primeira vez em uma máquina nova consome o state remoto automaticamente.
Não é necessário `-backend-config`, pois tudo está hardcoded em `providers.tf`.

## RBAC necessário

Para ler/gravar o state, o principal precisa de
**Storage Blob Data Contributor** em
`/subscriptions/.../rg-tfstate-nossodireito/.../stnossodireitobr`:

- Operador humano: usuário Azure AD (já concedido para o owner do projeto).
- Pipeline `terraform.yml`: Service Principal `sp-nossodireito-deploy`
  (concedido em 2026-05-31).

Para conceder a um novo operador:

```bash
SA_ID=$(az storage account show -n stnossodireitobr \
  -g rg-tfstate-nossodireito --query id -o tsv)

az role assignment create \
  --assignee <UPN-ou-objectId> \
  --role "Storage Blob Data Contributor" \
  --scope "$SA_ID"
```

## Recursos físicos do backend

| Recurso | Nome | Notas |
|---------|------|-------|
| Resource group | `rg-tfstate-nossodireito` | região `brazilsouth` |
| Storage account | `stnossodireitobr` | Standard_LRS, Cool, TLS1.2, public access OFF |
| Container | `tfstate` | private, blob versioning ATIVO |
| Blob key | `nossodireito.prod.tfstate` | state principal |

Proteções de durabilidade (ligadas em 2026-05-31):

- Blob versioning: **ATIVO** (toda escrita gera nova versão).
- Blob soft-delete: **7 dias**.
- Container soft-delete: **7 dias**.
- `tfstate/` não tem TTL.

## Provisionamento histórico (para replicar em outro ambiente)

```bash
az group create --name rg-tfstate-nossodireito --location brazilsouth

az storage account create \
  --name stnossodireitobr \
  --resource-group rg-tfstate-nossodireito \
  --location brazilsouth \
  --sku Standard_LRS --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --access-tier Cool

az storage container create \
  --name tfstate \
  --account-name stnossodireitobr \
  --auth-mode login
```

## Operações comuns

- **Listar locks ativos:** `az storage blob show -c tfstate -n nossodireito.prod.tfstate --account-name stnossodireitobr --auth-mode login --query "properties.lease" -o json`
- **Quebrar lease órfã (apenas em emergência):** `az storage blob lease break -b nossodireito.prod.tfstate -c tfstate --account-name stnossodireitobr --auth-mode login`
- **Snapshot manual:** `az storage blob snapshot -c tfstate -n nossodireito.prod.tfstate --account-name stnossodireitobr --auth-mode login`

## Referências

- <https://developer.hashicorp.com/terraform/language/backend/azurerm>
- <https://learn.microsoft.com/azure/storage/common/storage-auth-aad>
