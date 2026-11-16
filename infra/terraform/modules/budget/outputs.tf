output "budget_id" {
  description = "Id of the resource-group budget."
  value       = azurerm_consumption_budget_resource_group.this.id
}

output "notification_thresholds" {
  description = "Effective threshold ladder (percent of budget): actual thresholds then the forecast."
  value = concat(
    [for t in var.actual_thresholds : { threshold = t, type = "Actual" }],
    [{ threshold = var.forecast_threshold, type = "Forecasted" }],
  )
}
