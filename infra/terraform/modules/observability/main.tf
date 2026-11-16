# Monitoring resource group and the central Log Analytics workspace.
#
# Cost control is built into the workspace itself: retention is variable-
# validated into the cheapest interactive band (30-730 days) and a daily
# ingestion quota caps runaway data volumes. PerGB2018 is pay-as-you-go —
# no capacity reservation, no standing charge.
resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = var.workspace_name
  resource_group_name = azurerm_resource_group.this.name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = var.retention_in_days
  # Hard cap on daily ingestion (GB). The workspace stops ingesting
  # operator/agent data above the cap — the primary runaway-cost brake.
  daily_quota_gb = var.daily_quota_gb
  # Entra ID (Azure RBAC) only: no workspace-local primary/secondary keys.
  local_authentication_enabled = false
  # Queries must go through authenticated control-plane paths; block the
  # public query endpoint. Ingestion stays enabled because this scaffold has
  # no private link — the Azure Monitor pipeline needs a reachable path.
  internet_query_enabled     = false
  internet_ingestion_enabled = var.internet_ingestion_enabled
  tags                       = var.tags
}
