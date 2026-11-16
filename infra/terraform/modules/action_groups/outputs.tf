output "action_group_id" {
  description = "Id of the shared action group (alert + budget notification target)."
  value       = azurerm_monitor_action_group.this.id
}
