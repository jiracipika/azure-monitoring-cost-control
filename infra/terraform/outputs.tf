output "status" {
  description = "Lifecycle marker: all modules implemented offline, deploy gate closed."
  value       = "implemented-offline-gated"
}

output "workspace_id" {
  description = "Central Log Analytics workspace (query/data source for alerts)."
  value       = one(module.observability[*].workspace_id)
}

output "data_collection_rule_id" {
  description = "Data collection rule defining the collected streams."
  value       = one(module.data_collection[*].data_collection_rule_id)
}

output "action_group_id" {
  description = "Shared notification hub for alerts and budgets."
  value       = one(module.action_groups[*].action_group_id)
}

output "workbook_id" {
  description = "Investigation and tag-governance workbook."
  value       = one(module.workbook[*].workbook_id)
}

output "budget_notification_thresholds" {
  description = "Effective budget threshold ladder (percent + type)."
  value       = one(module.budget[*].notification_thresholds)
}
