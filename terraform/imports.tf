# ============================================================
# Terraform State Migration — Removed Blocks (TF 1.7+)
# ============================================================
# Recursos removidos do código mas mantidos no Azure para limpeza
# manual posterior. `lifecycle.destroy = false` impede o TF de tentar
# deletar (que falharia por falta de permissão do GHA SP, e mesmo se
# tivesse não há urgência — Doc Intelligence F0 = custo zero).
#
# Para limpeza manual quando conveniente:
#   az role assignment delete --ids \
#     /subscriptions/<sub>/resourceGroups/rg-nossodireito-br/providers/Microsoft.CognitiveServices/accounts/cog-nossodireito-br-docint/providers/Microsoft.Authorization/roleAssignments/1f47605c-655e-c325-96cd-1794fbc58d43
#   az cognitiveservices account delete \
#     -n cog-nossodireito-br-docint -g rg-nossodireito-br --yes
# ============================================================

removed {
  from = azurerm_cognitive_account.doc_intelligence
  lifecycle {
    destroy = false
  }
}

removed {
  from = azurerm_role_assignment.app_to_doc_intelligence
  lifecycle {
    destroy = false
  }
}
