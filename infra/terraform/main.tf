# Root module of the Monitoring and Cost Control stack. EVERY Azure
# resource is gated behind deploy_enabled (default false): with default
# variables `terraform plan` proposes zero changes outside the placeholder
# provider configuration.
#
# Wiring order: observability (workspace + retention/quota caps) ->
# data collection (DCR streams into the workspace) -> diagnostics
# (workspace self-audit aggregated into the same workspace) ->
# action groups (single notification hub) -> alert rules (KQL + Service
# Health) -> budget (escalating thresholds on the resource group) ->
# workbook (investigation + tag governance reporting).

locals {
  project = "azure-monitoring-cost-control"
  tags = merge(var.tags, {
    project = local.project
  })
}

# --- Central workspace with retention + ingestion caps ---------------------------
module "observability" {
  count = var.deploy_enabled ? 1 : 0

  source = "./modules/observability"

  resource_group_name = "rg-mon-central"
  workspace_name      = "log-mon-central"
  location            = var.location
  retention_in_days   = var.log_analytics_retention_days
  daily_quota_gb      = var.daily_quota_gb
  tags                = local.tags
}

# --- What gets collected: counters + error syslog -------------------------------
module "data_collection" {
  count = var.deploy_enabled ? 1 : 0

  source = "./modules/data_collection"

  name                  = "dcr-mon-central"
  location              = var.location
  resource_group_name   = one(module.observability[*].resource_group_name)
  workspace_resource_id = one(module.observability[*].workspace_id)
  perf_sampling_seconds = var.perf_sampling_seconds
  tags                  = local.tags
}

# --- Diagnostic settings aggregation: the workspace audits itself ----------------
module "diagnostics" {
  count = var.deploy_enabled ? 1 : 0

  source = "./modules/diagnostics"

  name                  = "diag-workspace-audit"
  target_resource_id    = one(module.observability[*].workspace_id)
  workspace_resource_id = one(module.observability[*].workspace_id)
  log_categories        = ["Audit", "Usage"]
  metric_categories     = []
}

# --- One notification hub for every alert ----------------------------------------
module "action_groups" {
  count = var.deploy_enabled ? 1 : 0

  source = "./modules/action_groups"

  name                = "ag-mon-central"
  short_name          = "costmon"
  resource_group_name = one(module.observability[*].resource_group_name)
  alert_emails        = var.alert_emails
  tags                = local.tags
}

# --- KQL alert rules + Service Health --------------------------------------------
module "alert_rules" {
  count = var.deploy_enabled ? 1 : 0

  source = "./modules/alert_rules"

  resource_group_name      = one(module.observability[*].resource_group_name)
  location                 = var.location
  workspace_data_source_id = one(module.observability[*].workspace_id)
  action_group_id          = one(module.action_groups[*].action_group_id)
  subscription_id          = var.azure_subscription_id
  tags                     = local.tags
}

# --- Spend guardrail: escalating budget thresholds -------------------------------
module "budget" {
  count = var.deploy_enabled ? 1 : 0

  source = "./modules/budget"

  resource_group_id   = one(module.observability[*].resource_group_id)
  resource_group_name = one(module.observability[*].resource_group_name)
  amount              = var.budget_amount
  actual_thresholds   = var.budget_actual_thresholds
  forecast_threshold  = var.budget_forecast_threshold
  alert_emails        = var.alert_emails
  action_group_id     = one(module.action_groups[*].action_group_id)
}

# --- Investigation + governance reporting surface --------------------------------
module "workbook" {
  count = var.deploy_enabled ? 1 : 0

  source = "./modules/workbook"

  name                  = "wb-mon-central"
  display_name          = "Monitoring and Cost Control"
  resource_group_name   = one(module.observability[*].resource_group_name)
  location              = var.location
  workspace_resource_id = one(module.observability[*].workspace_id)
  required_tags         = var.required_tags
  tags                  = local.tags
}
