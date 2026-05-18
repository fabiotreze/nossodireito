# --- Terraform Import Blocks (Terraform 1.5+) ---
# Recursos criados fora do TF que precisam ser adotados pelo state.
# Após apply bem-sucedido, este arquivo pode ser removido (ou mantido como registro).

# Doc Intelligence foi criado manualmente antes do TF cobri-lo.
# Importa para o state em vez de tentar recriar.
import {
  to = azurerm_cognitive_account.doc_intelligence[0]
  id = "/subscriptions/${var.subscription_id}/resourceGroups/${local.resource_group_name}/providers/Microsoft.CognitiveServices/accounts/cog-${local.project}-docint${local.suffix}"
}
