# GLM implementation instructions — Monitoring and Cost Control

**Architecture:** Azure Monitor and Log Analytics collect telemetry from VMs/AKS/App Service/SQL -> KQL -> actionable alerts, Azure Workbooks and cost budgets.

**Goal:** Demonstrate error investigations, appropriate alerts and controlled dev-environment spend.

## Offline implementation backlog

- [x] Audit existing files, Azure documentation and actual available tools
  (provider schema verified via `terraform providers schema -json`;
  azurerm 4.81.0 exposes workbooks as `azurerm_application_insights_workbook`,
  scheduled query rules use numeric `frequency`/`time_window` and a set-valued
  `action.action_group`). — 2026-11-16
- [x] Implement realistic modular IaC for all named services; leave
  `deploy_enabled=false` as default. Seven modules: `observability`
  (workspace: PerGB2018, 30-730d retention validation, daily quota, no local
  keys, public query closed), `data_collection` (DCR: counters + error
  syslog -> workspace only), `diagnostics` (workspace-only aggregation),
  `action_groups` (email, common schema), `alert_rules` (KQL CPU/syslog
  alerts + Service Health), `budget` (Actual 50/80 + Forecasted 100 with
  emails + action group), `workbook` (triage + Usage + untagged-resources
  reporting from required_tags). — 2026-11-16
- [x] Implement deterministic offline demo covering error investigations,
  appropriate alerts and controlled dev-environment spend:
  `tests/monitor_simulator.py` parses the REAL budget ladder and alert
  rules, then replays spend trajectories (Actual vs Forecasted semantics,
  strict GreaterThan) and metric series (fired/resolved state machine with
  auto-mitigation hysteresis) — 23 scenario tests in
  `tests/test_monitor_sim.py`. — 2026-11-16
- [x] Create behavior, failure and negative-security tests: 74 tests across
  `tests/test_scaffold.py`, `tests/test_monitoring.py` (retention capped,
  no diagnostic-to-storage, thresholds ordered/unique, alert queries
  restricted to DCR-ingested tables, gate/CI safety),
  `tests/test_monitor_sim.py`, `tests/test_security_scan.py`. — 2026-11-16
- [x] Add static security scanners, dependency review and minimal CI
  permissions; pin tested action versions: in-repo scanner
  (`tests/test_security_scan.py`: credential patterns, pinned action tags,
  no pull_request_target, placeholder-only GUIDs, hygiene incl.
  environments-tfvars gating and .mimosa), provider dependency review via
  committed `.terraform.lock.hcl` (azurerm 4.81.0), workflow
  `permissions: contents: read`, actions pinned to version tags. — 2026-11-16
- [x] Refine topology diagram, network/identity trust boundaries and
  disaster recovery paths: `diagrams/architecture.mmd` matches the seven
  modules; trust boundaries + residual risks in docs/SECURITY.md; teardown
  order (workspace last, data irreversible) in docs/TEARDOWN.md. — 2026-11-16
- [x] Run unittest, terraform fmt, init -backend=false, validate and
  document real output — 74 tests OK, fmt/init/validate green, four
  failure groups found+fixed recorded in docs/VALIDATION.md. — 2026-11-16

## Cost gate

- [x] Estimate fixed and variable regional Azure costs; verify licenses and
  quotas — indicative ~US$5-15/mo realistic, ~US$345/mo theoretical quota
  ceiling, in docs/COSTS.md (offline list-price estimate; verify at
  approval time). 2026-11-16
- [ ] Require explicit approval for exact deployment scope, maximum budget
  and teardown. (Awaiting owner.)
- [ ] Only after approval may live testing, performance measurements and
  cost validation occur.

## Next milestone candidates (offline, no approval needed)

- Metric-alert coverage (e.g. workspace near-quota) once pricing for log vs
  metric alerts is verified.
- Azure Monitor Agent association wiring (DCR -> VM) as a parameterized
  module for when workload repos land VMs.
- Private data collection endpoint + `internet_ingestion_enabled = false`
  flip-plan (documented in SECURITY.md residual risks).

Don't stop at proposals. Start implementing an offline slice now and submit evidence.
