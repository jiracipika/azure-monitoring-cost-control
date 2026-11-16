# Cost gate for the monitoring resource group. A budget NEVER stops
# billing — it notifies. Escalating Actual thresholds catch in-progress
# overrun; a 100% Forecasted threshold warns before the month ends when
# the run-rate trajectory points past the cap.
#
# Notifications reach BOTH the alert emails and the shared action group,
# so budget events ride the same on-call path as technical alerts.
resource "azurerm_consumption_budget_resource_group" "this" {
  name              = "budget-${var.resource_group_name}"
  resource_group_id = var.resource_group_id
  amount            = var.amount
  time_grain        = "Monthly"

  time_period {
    # First day of the first month after this milestone (2026-11); budgets
    # cannot start in the past.
    start_date = "2026-12-01T00:00:00Z"
  }

  # Escalating actual-spend thresholds (50% -> 80% by default).
  dynamic "notification" {
    for_each = var.actual_thresholds
    content {
      enabled        = true
      operator       = "GreaterThan"
      threshold      = notification.value
      threshold_type = "Actual"
      contact_emails = var.alert_emails
      contact_groups = var.action_group_id != "" ? [var.action_group_id] : []
    }
  }

  # Forecasted end-of-month spend crossing the cap — the early warning.
  notification {
    enabled        = true
    operator       = "GreaterThan"
    threshold      = var.forecast_threshold
    threshold_type = "Forecasted"
    contact_emails = var.alert_emails
    contact_groups = var.action_group_id != "" ? [var.action_group_id] : []
  }
}
