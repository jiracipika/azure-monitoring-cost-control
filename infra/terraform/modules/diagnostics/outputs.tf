output "diagnostic_setting_id" {
  description = "Id of the aggregated diagnostic setting."
  value       = azurerm_monitor_diagnostic_setting.this.id
}
