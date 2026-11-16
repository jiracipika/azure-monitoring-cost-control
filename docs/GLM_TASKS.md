# GLM implementation instructions — Monitoring and Cost Control

**Architecture:** Azure Monitor and Log Analytics collect telemetry from VMs/AKS/App Service/SQL -> KQL -> actionable alerts, Azure Workbooks and cost budgets.

**Goal:** Demonstrate error investigations, appropriate alerts and controlled dev-environment spend.

## Offline implementation backlog
- [ ] Audit existing files, Azure documentation and actual available tools.
- [ ] Implement realistic modular IaC for all named services; leave deploy_enabled=false as default.
- [ ] Implement deterministic offline demo covering demonstrate error investigations, appropriate alerts and controlled dev-environment spend.
- [ ] Create behavior, failure and negative-security tests.
- [ ] Add static security scanners, dependency review and minimal CI permissions; pin tested action versions.
- [ ] Refine topology diagram, network/identity trust boundaries and disaster recovery paths.
- [ ] Run unittest, terraform fmt, init -backend=false, validate and document real output.

## Cost gate
- [ ] Estimate fixed and variable regional Azure costs; verify licenses and quotas.
- [ ] Require explicit approval for exact deployment scope, maximum budget and teardown.
- [ ] Only after approval may live testing, performance measurements and cost validation occur.

Don't stop at proposals. Start implementing an offline slice now and submit evidence.
