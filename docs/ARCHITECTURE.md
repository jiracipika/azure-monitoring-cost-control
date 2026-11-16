# Architecture

Azure Monitor and Log Analytics collect telemetry from VMs/AKS/App Service/SQL -> KQL -> actionable alerts, Azure Workbooks and cost budgets.

**Acceptance goal:** Demonstrate error investigations, appropriate alerts and controlled dev-environment spend.

**Status:** implemented offline as seven gated Terraform modules. NOT deployed — every module sits behind `deploy_enabled = false` (default), so a plan with default variables proposes zero Azure resources.

## Module map (infra/terraform/modules/)

| Module | Resources | Purpose |
|---|---|---|
| `observability` | resource group + Log Analytics workspace | Central telemetry sink. Cost brakes built in: `PerGB2018` pay-as-you-go SKU, retention validated to 30–730 days, `daily_quota_gb` ingestion cap, `local_authentication_enabled = false` (Entra ID only), public query endpoint closed. |
| `data_collection` | `azurerm_monitor_data_collection_rule` | Declares WHAT is collected: CPU + memory counters (60s sampling floor) and error-and-worse syslog; destinations: Log Analytics only. Stream set is exactly `Microsoft-Perf` + `Microsoft-Syslog` — the closed set of tables alert queries may reference (test-enforced). |
| `diagnostics` | `azurerm_monitor_diagnostic_setting` | Diagnostic settings aggregation into the workspace. Wired in-repo to the workspace itself (Audit + Usage categories) so control-plane activity and ingestion volume are queryable. Destination is workspace-only — never storage (test-enforced). |
| `action_groups` | `azurerm_monitor_action_group` | Single notification hub (email receivers only, common alert schema) shared by query alerts, Service Health and budget notifications. |
| `alert_rules` | 2x `azurerm_monitor_scheduled_query_rules_alert` + `azurerm_monitor_activity_log_alert` | Error investigation alerts: sustained CPU (sev 2) and syslog error burst (sev 1), both 5-minute frequency over a 15-minute window with auto-mitigation; Service Health alert (Incident/Maintenance/Informational/ActionRequired, region-filtered) scoped to the subscription. |
| `budget` | `azurerm_consumption_budget_resource_group` | Escalating Actual thresholds (default 50% -> 80%) plus a 100% Forecasted early warning; notifications to emails AND the action group. A budget notifies — it never stops billing. |
| `workbook` | `azurerm_application_insights_workbook` | Investigation + governance surface: CPU by host, syslog errors by host, ingestion by data type (Usage), untagged resources (Azure Resource Graph query generated from `required_tags` = environment, costCenter). |

Note: in azurerm 4.x workbooks are `azurerm_application_insights_workbook` — `azurerm_monitor_workbook` does not exist in 4.81.0 (verified via `terraform providers schema -json`).

## Data flow

1. Azure Monitor Agent (future VMs/AKS/App Service/SQL) -> data collection rule -> workspace (`Perf`, `Syslog`).
2. Platform telemetry (workspace Audit/Usage) -> diagnostic setting -> same workspace (aggregation).
3. KQL alert rules query the workspace every 5 minutes -> action group -> email.
4. Budget evaluates the resource group monthly -> thresholds -> emails + action group.
5. Workbook renders investigation + tag-governance views over the same tables.

## Trust boundaries and assumptions

- **Ingestion endpoint**: public ingestion stays ENABLED (`internet_ingestion_enabled`) because this scaffold has no private link / data collection endpoint; the public QUERY endpoint is closed and workspace-local keys are disabled. Before production: add a private data collection endpoint and flip ingestion off.
- **Identity**: Entra ID only for workspace access; no managed identity is created yet (the DCR needs no identity; DINE-style remediation identities are out of scope here).
- **CI credentials**: none. The workflow runs read-only offline checks; no OIDC, no secrets.
- **Region**: canadacentral; Service Health events filtered to it.
- **Placeholders**: subscription/tenant ids are all-zero GUIDs; replace via tfvars before any approved deployment.

This is an offline scaffold, NOT deployed production architecture.
