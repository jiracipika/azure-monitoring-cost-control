# Azure Workbook: the "read the room" surface for error investigations and
# cost/tag governance. Three query tiles:
#   1. CPU by host (Perf)   — what the high-CPU alert sees
#   2. syslog errors by host (Syslog) — what the burst alert sees
#   3. ingestion volume by data type (Usage) — what drives workspace cost
#   4. untagged resources (Azure Resource Graph) — tag governance reporting
# The tag query is generated from var.required_tags so the workbook and the
# governance rules cannot drift apart.
#
# NOTE: in azurerm 4.x workbooks are exposed as
# azurerm_application_insights_workbook (verified via `terraform providers
# schema -json`; azurerm_monitor_workbook does not exist in 4.81.0).
locals {
  missing_tag_conditions = join(
    " or ",
    [for tag in var.required_tags : format("isempty(tags['%s'])", tag)],
  )

  workbook = {
    version = "Notebook/1.0"
    items = [
      {
        type = 1
        name = "overview"
        content = {
          json = format(
            "# Monitoring and Cost Control\n\nTelemetry collected by the data collection rule; alerts fire through the shared action group; spend is capped by notifications, not enforcement. Tag governance requires: %s.",
            join(", ", var.required_tags),
          )
        }
      },
      {
        type = 3
        name = "cpu-by-host"
        content = {
          version = "KqlItem/1.0"
          query   = "Perf | where ObjectName == \"Processor\" and CounterName == \"% Processor Time\" and InstanceName == \"_Total\" | summarize CPU = round(avg(CounterValue), 1) by Computer, bin(TimeGenerated, 5m)"
          size    = 1
        }
      },
      {
        type = 3
        name = "syslog-errors-by-host"
        content = {
          version = "KqlItem/1.0"
          query   = "Syslog | where SeverityLevel <= 3 | summarize Errors = count() by Computer, bin(TimeGenerated, 1h)"
          size    = 1
        }
      },
      {
        type = 3
        name = "ingestion-by-data-type"
        content = {
          version = "KqlItem/1.0"
          query   = "Usage | where TimeGenerated > ago(30d) | summarize Quantity = round(sum(Quantity), 2) by DataType | order by Quantity desc"
          size    = 1
        }
      },
      {
        type    = 3
        name    = "untagged-resources"
        subType = "KqlResourceGraph"
        content = {
          version = "KqlItem/1.0"
          query = format(
            "Resources | where %s | summarize count() by type | order by count_ desc",
            local.missing_tag_conditions,
          )
          size = 1
        }
      },
    ]
    isLocked            = false
    fallbackResourceIds = [var.workspace_resource_id]
  }
}

resource "azurerm_application_insights_workbook" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  display_name        = var.display_name
  category            = "workbook"
  source_id           = var.workspace_resource_id
  data_json           = jsonencode(local.workbook)
  tags                = var.tags
}
