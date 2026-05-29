# ============================================================
# Backend remoto (Azure Storage) — guia operacional
# ============================================================
# Este projeto opera, por padrão, com backend local + state
# persistido como artifact no GitHub Actions
# (ver `.github/workflows/terraform.yml`).
#
# Para postura de produção/compliance, recomenda-se migrar para
# Azure Storage com state lock nativo. Procedimento abaixo é
# opt-in e não exige alteração de código:
#
# 1) Provisionar (uma única vez) o storage de state:
#
#      az group create \
#        --name rg-tfstate-nossodireito \
#        --location brazilsouth
#
#      az storage account create \
#        --name sttfstatenossodireito \
#        --resource-group rg-tfstate-nossodireito \
#        --location brazilsouth \
#        --sku Standard_LRS \
#        --kind StorageV2 \
#        --min-tls-version TLS1_2 \
#        --allow-blob-public-access false
#
#      az storage container create \
#        --name tfstate \
#        --account-name sttfstatenossodireito \
#        --auth-mode login
#
# 2) Adicionar (em branch dedicada de migração) o bloco
#    `backend "azurerm" {}` ao terraform { ... } em providers.tf.
#
# 3) Rodar:
#
#      terraform init -reconfigure \
#        -backend-config="resource_group_name=rg-tfstate-nossodireito" \
#        -backend-config="storage_account_name=sttfstatenossodireito" \
#        -backend-config="container_name=tfstate" \
#        -backend-config="key=nossodireito.prod.tfstate" \
#        -backend-config="use_oidc=true" \
#        -backend-config="use_azuread_auth=true"
#
#    Aceitar a migração do state quando solicitado pelo Terraform.
#
# 4) Atualizar o pipeline `.github/workflows/terraform.yml` para
#    usar `-backend-config` no init e remover o upload/download
#    do artifact de state.
#
# Referências:
#   https://developer.hashicorp.com/terraform/language/backend/azurerm
#   https://learn.microsoft.com/azure/storage/common/storage-auth-aad
# ============================================================
