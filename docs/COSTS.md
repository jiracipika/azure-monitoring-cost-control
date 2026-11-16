# Azure cost gate

Authorized Azure spend: **$0**. No resources deployed. Budgets notify rather than enforce a hard spending ceiling. Request approval for every chargeable deployment.

## Offline estimate for the implemented stack (indicative list prices, canadacentral — VERIFY against the Azure Monitor pricing page before any approval; labels: estimated)

| Item | Basis | Estimate |
|---|---|---|
| Log Analytics ingestion (PerGB2018) | ~US$2.30/GB list (estimated); first 5 GB/month per subscription free | dev volume (2 counters @60s + error syslog on 1-3 VMs): tens-to-hundreds of MB/day -> **< US$5/mo** |
| Long retention | we default 30 days (free interactive band) | US$0; each 31+ day band adds ~US$0.10-0.12/GB/mo (estimated) |
| Daily quota ceiling | 5 GB/day hard stop on ingestion | worst case if constantly maxed: ~150 GB/mo -> ~US$345/mo — the ceiling the quota allows, NOT expected dev volume |
| Workbooks, action groups, activity log alerts, data collection rules, budgets | platform free tier | US$0 |
| Log-search alert rules (2) | historically a small per-rule charge (verify current "Alerts (log)" pricing) | ~US$0.10-1/mo (estimated) |
| **Realistic monthly total** | dev-size environment | **~US$5-15/mo (estimated)** |

Controls that make the estimate defensible:

1. `daily_quota_gb = 5` — workspace stops ingesting past the cap (the only true hard limit in the design).
2. Budget ladder on the resource group: Actual 50% -> 80%, Forecasted 100% of the default 20 CAD budget, to emails + action group.
3. Syslog collection restricted to error-and-worse; counter sampling floor 60s (variable-validated) — both keep the biggest ingestion drivers small by construction.
4. Simulator evidence (tests/test_monitor_sim.py): which thresholds fire for a given spend trajectory is proven offline, so the ladder is auditable before it exists.

## Approval gate

- [x] Fixed + variable regional costs estimated above (indicative; verify at approval time)
- [ ] Explicit owner approval for exact deployment scope, maximum budget and teardown
- [ ] Only after approval: live testing, performance measurements, cost validation

Licenses/quotas: no special licenses. Quota to verify pre-deploy: none expected (no VMs); Log Analytics per-subscription free-tier tracking applies.
