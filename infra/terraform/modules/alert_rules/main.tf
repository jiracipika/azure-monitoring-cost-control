# Alert pack. Two log-search alert rules over the tables the data
# collection rule actually ingests (Perf, Syslog — enforced by
# tests/test_monitoring.py against the real HCL), plus a Service Health
# activity log alert scoped to the subscription.
#
# Rule semantics (azurerm 4.x, verified against the provider schema):
#   frequency  5  — evaluate every 5 minutes (plain number of minutes)
#   time_window 15 — look back over the last 15 minutes (plain number of minutes)
#   trigger    GreaterThan N against the query's aggregated value
#   auto_mitigation_enabled — resolves the alert once the condition clears
#     for a full window (the hysteresis tests/test_monitor_sim.py models).

# --- Error investigation: sustained CPU saturation -----------------------------
resource "azurerm_monitor_scheduled_query_rules_alert" "high_cpu" {
  name                = "sq-high-cpu-sustained"
  location            = var.location
  resource_group_name = var.resource_group_name

  data_source_id = var.workspace_data_source_id
  query          = <<-KQL
    Perf
    | where ObjectName == "Processor" and CounterName == "% Processor Time" and InstanceName == "_Total"
    | summarize AggregatedValue = avg(CounterValue) by bin(TimeGenerated, 5m)
  KQL
  severity       = 2
  frequency      = 5
  time_window    = 15
  description    = "Average CPU above threshold for the evaluation window — see the error-triage workbook section."

  action {
    action_group = [var.action_group_id]
  }

  trigger {
    operator  = "GreaterThan"
    threshold = var.high_cpu_threshold_pct
  }

  auto_mitigation_enabled = true
  tags                    = var.tags
}

# --- Error investigation: syslog error burst per host ---------------------------
resource "azurerm_monitor_scheduled_query_rules_alert" "syslog_error_burst" {
  name                = "sq-syslog-error-burst"
  location            = var.location
  resource_group_name = var.resource_group_name

  data_source_id = var.workspace_data_source_id
  query          = <<-KQL
    Syslog
    | where SeverityLevel <= 3
    | summarize AggregatedValue = count() by Computer, bin(TimeGenerated, 5m)
  KQL
  severity       = 1
  frequency      = 5
  time_window    = 15
  description    = "More than the threshold of error-or-worse syslog records from one host inside the window."

  action {
    action_group = [var.action_group_id]
  }

  trigger {
    operator  = "GreaterThan"
    threshold = var.syslog_error_threshold
  }

  auto_mitigation_enabled = true
  tags                    = var.tags
}

# --- Service Health: platform incidents reach the on-call path ------------------
# Activity log alerts are created at the subscription scope; the resource
# itself lives in the "global" location per the Azure Monitor API.
resource "azurerm_monitor_activity_log_alert" "service_health" {
  name                = "alh-service-health"
  location            = "global"
  resource_group_name = var.resource_group_name
  scopes              = ["/subscriptions/${var.subscription_id}"]
  description         = "Azure Service Health incidents, maintenance, informational and action-required events."

  criteria {
    category = "ServiceHealth"

    service_health {
      events    = ["ActionRequired", "Incident", "Informational", "Maintenance"]
      locations = [var.location]
      services  = ["All"]
    }
  }

  action {
    action_group_id = var.action_group_id
  }

  tags = var.tags
}
