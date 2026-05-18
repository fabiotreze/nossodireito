# ============================================================
# DEPRECATED — Azure Document Intelligence (substituído por Azure OpenAI)
# ============================================================
# Histórico:
# - v1.16.0: introduzido como backend de análise IA via prebuilt-read
# - v1.18.0: REMOVIDO — `prebuilt-read` é OCR e rejeita text/plain
#            (erro: "Invalid request."). Substituído por Azure OpenAI
#            gpt-4o-mini em ai-openai.tf
#
# As variáveis abaixo permanecem para preservar a referência simbólica
# do app_settings legacy (`local.doc_intelligence_app_settings`), mas
# o bloco `local` resolve para mapa vazio — não injeta env vars.
#
# Os recursos físicos (`azurerm_cognitive_account.doc_intelligence` +
# `azurerm_role_assignment.app_to_doc_intelligence`) foram removidos
# do state via `removed` blocks em imports.tf. Os objetos no Azure
# permanecem (free tier F0 = $0) e podem ser deletados manualmente:
#   az cognitiveservices account delete \
#     -n cog-nossodireito-br-docint -g rg-nossodireito-br
# ============================================================

variable "enable_ai_doc_intelligence" {
  description = "DEPRECATED v1.18.0 — substituído por Azure OpenAI (vide ai-openai.tf)"
  type        = bool
  default     = false
}

variable "ai_doc_intelligence_sku" {
  description = "DEPRECATED v1.18.0 — não tem efeito"
  type        = string
  default     = "F0"
}

# Mapa vazio para compat — o merge em main.tf continua funcionando sem
# precisar editar todas as referências de uma só vez.
locals {
  doc_intelligence_app_settings = {}
}
