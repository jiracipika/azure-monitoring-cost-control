output "data_collection_rule_id" {
  description = "Id of the data collection rule (association target for future Azure Monitor Agents)."
  value       = azurerm_monitor_data_collection_rule.this.id
}

output "streams" {
  description = "Streams collected — the closed set of tables alert queries may reference."
  value       = ["Microsoft-Perf", "Microsoft-Syslog"]
}
