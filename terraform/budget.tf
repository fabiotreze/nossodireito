# ============================================================
# Budget — Subscription-scoped cost alert
# ============================================================
# MS-AZR-0062P (Visual Studio Enterprise) — crédito mensal ~$150 USD.
# Default: 70% threshold → e-mail antes do crédito esgotar (subscription
# é suspensa em 100%).
#
# Notificações:
#   - Actual ≥ 70%      → gasto real ultrapassou o limite
#   - Forecasted ≥ 70%  → projeção mensal indica que vai ultrapassar
#
# Ativar setando `monthly_budget_amount > 0` no tfvars.
# ============================================================

resource "azurerm_consumption_budget_subscription" "main" {
  count = var.monthly_budget_amount > 0 ? 1 : 0

  name            = "budget-${local.project}${local.suffix}-${var.budget_alert_threshold}pct"
  subscription_id = "/subscriptions/${var.subscription_id}"

  amount     = var.monthly_budget_amount
  time_grain = "Monthly"

  time_period {
    # Início do mês corrente em UTC. end_date opcional (default: 10 anos).
    start_date = formatdate("YYYY-MM-01'T'00:00:00'Z'", timestamp())
    end_date   = "2030-12-31T00:00:00Z"
  }

  # Alert 1 — Gasto real ultrapassou o threshold
  notification {
    enabled        = true
    threshold      = var.budget_alert_threshold
    operator       = "GreaterThan"
    threshold_type = "Actual"

    contact_emails = var.alert_email != "" ? [var.alert_email] : []
    contact_roles  = ["Owner"]
  }

  # Alert 2 — Projeção mensal indica que vai ultrapassar
  notification {
    enabled        = true
    threshold      = var.budget_alert_threshold
    operator       = "GreaterThan"
    threshold_type = "Forecasted"

    contact_emails = var.alert_email != "" ? [var.alert_email] : []
    contact_roles  = ["Owner"]
  }

  # start_date muda a cada plan (timestamp()) — ignora drift cosmético.
  lifecycle {
    ignore_changes = [time_period[0].start_date]
  }
}
