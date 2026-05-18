# ============================================================
# Terraform State Migration — Removed Blocks (TF 1.7+)
# ============================================================
# Recursos do antigo Doc Intelligence removidos do código HCL.
# `lifecycle.destroy = false` mantém os blocos `removed` válidos
# mesmo após a limpeza física.
#
# Limpeza física concluída em v1.18.1 (2026-05-18):
#   - cog-nossodireito-br-docint: DELETADO + PURGADO
#   - role assignment associada: removida automaticamente com o recurso pai
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
