# Azure Monitor data collection: the rule defines WHAT the Azure Monitor
# Agent sends and WHERE it lands. Deliberately minimal to keep ingestion
# cost predictable:
#   - performance counters: CPU + memory, sampled every 60s
#   - syslog: warning-and-worse for common facilities (error investigation)
# Destinations: Log Analytics ONLY. No storage account, no event hub —
# nothing lands in a publicly reachable sink (see tests/test_monitoring.py).
resource "azurerm_monitor_data_collection_rule" "this" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  description         = "CPU/memory counters and error-level syslog to the central workspace"
  tags                = var.tags

  data_sources {
    performance_counter {
      name                          = "cpu-and-memory-counters"
      streams                       = ["Microsoft-Perf"]
      sampling_frequency_in_seconds = var.perf_sampling_seconds
      counter_specifiers = [
        "\\Processor(_Total)\\% Processor Time",
        "\\Memory\\Available Bytes",
      ]
    }

    syslog {
      name           = "error-syslog"
      streams        = ["Microsoft-Syslog"]
      facility_names = ["auth", "cron", "daemon", "kern", "syslog", "user"]
      log_levels     = ["Alert", "Critical", "Emergency", "Error", "Warning"]
    }
  }

  destinations {
    log_analytics {
      name                  = "central-workspace"
      workspace_resource_id = var.workspace_resource_id
    }
  }

  data_flow {
    streams      = ["Microsoft-Perf", "Microsoft-Syslog"]
    destinations = ["central-workspace"]
  }
}
