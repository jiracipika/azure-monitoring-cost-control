# Teardown

No Azure resources deployed (deploy gate closed). This is the plan for any future APPROVED deployment of the implemented stack.

## Destroy order (dependency-aware, least-destructive first)

1. **Alerting** (`modules/alert_rules`): query alerts, Service Health alert — delete first so teardown noise cannot page anyone.
2. **Workbook** (`modules/workbook`) — reporting only, no data.
3. **Budget** (`modules/budget`) — deleting it stops cost notifications; note spend already accrued still bills.
4. **Diagnostics** (`modules/diagnostics`) — remove the aggregation setting before its target disappears.
5. **Data collection** (`modules/data_collection`) — the DCR; any Azure Monitor Agent associations must be removed with (or before) their VMs.
6. **Workspace + resource group** (`modules/observability`) — LAST and irreversible: deleting the Log Analytics workspace deletes every collected log. Export anything needed for post-mortems first (workbook export or Log Analytics export).

All resources live in one resource group (`rg-mon-central`), so `terraform destroy` with the approved state covers the full set; the order above matters only for staged manual cleanup or incident teardown.

## Post-teardown inspection checklist

- Budget history/accrued charges in Cost Management (a deleted budget stops alerting, not billing).
- Orphaned items to inspect: none expected (no public IPs, disks, gateways or SQL in scope), but verify no external DCR associations survived their VMs.
- State: remove the Terraform state entry only after confirming the resource group is gone.

Rollback for a partial teardown: re-run `terraform apply` with the same variables — everything in this stack is recreatable except workspace DATA.
