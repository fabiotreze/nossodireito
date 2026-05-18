# ============================================================
# DEPRECATED — Azure Document Intelligence (substituído por Azure OpenAI)
# ============================================================
# Histórico:
# - v1.16.0: introduzido como backend de análise IA via prebuilt-read
# - v1.18.0: REMOVIDO — `prebuilt-read` é OCR e rejeita text/plain
#            (erro: "Invalid request."). Substituído por Azure OpenAI
#            gpt-4o-mini em ai-openai.tf
# - v1.18.1: recurso `cog-nossodireito-br-docint` DELETADO + PURGADO
#            do Azure (delete+purge manual em 2026-05-18). Este
#            arquivo é mantido apenas como placeholder histórico —
#            não declara nenhum recurso.
#
# Os blocos `removed` já reconciliaram o state em imports.tf.
# Pode ser apagado completamente em uma futura limpeza do repo.
# ============================================================


# Mapa vazio para compat — o merge em main.tf continua funcionando sem
# precisar editar todas as referências de uma só vez.
locals {
  doc_intelligence_app_settings = {}
}
