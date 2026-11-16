# Offline-safe defaults: the deploy gate stays closed. To prepare a real
# deployment (owner approval required first), set deploy_enabled = true,
# provide azure_subscription_id / azure_tenant_id and real alert_emails via
# -var-file / environment, then review terraform plan BEFORE any apply.
deploy_enabled               = false
location                     = "canadacentral"
log_analytics_retention_days = 30
daily_quota_gb               = 5
budget_amount                = 20
budget_actual_thresholds     = [50, 80]
budget_forecast_threshold    = 100
alert_emails                 = ["ops-team@example.invalid"]
