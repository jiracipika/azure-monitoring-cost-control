output "high_cpu_alert_id" {
  description = "Id of the sustained-CPU query alert."
  value       = azurerm_monitor_scheduled_query_rules_alert.high_cpu.id
}

output "syslog_burst_alert_id" {
  description = "Id of the syslog error-burst query alert."
  value       = azurerm_monitor_scheduled_query_rules_alert.syslog_error_burst.id
}

output "service_health_alert_id" {
  description = "Id of the Service Health activity log alert."
  value       = azurerm_monitor_activity_log_alert.service_health.id
}
