output "workbook_id" {
  description = "Id of the governance/investigation workbook."
  value       = azurerm_application_insights_workbook.this.id
}
