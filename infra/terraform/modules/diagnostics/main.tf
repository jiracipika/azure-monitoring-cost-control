# Diagnostic settings aggregation: replays a target resource's platform
# telemetry into the central workspace. Attached in-repo to the Log
# Analytics workspace itself (Audit + Usage categories) so workspace
# control-plane activity and ingestion volume are queryable alongside
# workload telemetry.
#
# Destination is Log Analytics ONLY — never a storage account. Diagnostic
# settings with a storage destination land data in a container whose
# account-level public-network posture is easy to get wrong; tests assert
# this module never wires any storage destination attribute.
resource "azurerm_monitor_diagnostic_setting" "this" {
  name                       = var.name
  target_resource_id         = var.target_resource_id
  log_analytics_workspace_id = var.workspace_resource_id
  # Dedicated tables (AzureDiagnostics-style per-category tables) instead
  # of the legacy combined AzureMetrics blob.
  log_analytics_destination_type = "Dedicated"

  dynamic "enabled_log" {
    for_each = var.log_categories
    content {
      category = enabled_log.value
      retention_policy {
        enabled = false
      }
    }
  }

  dynamic "enabled_metric" {
    for_each = var.metric_categories
    content {
      category = enabled_metric.value
    }
  }
}
