output "resource_group_id" {
  description = "Id of the monitoring resource group (budget scope)."
  value       = azurerm_resource_group.this.id
}

output "resource_group_name" {
  description = "Name of the monitoring resource group."
  value       = azurerm_resource_group.this.name
}

output "workspace_id" {
  description = "Resource id of the central workspace (destination for DCR, diagnostics and alert queries)."
  value       = azurerm_log_analytics_workspace.this.id
}
