# Architecture

Azure Monitor and Log Analytics collect telemetry from VMs/AKS/App Service/SQL -> KQL -> actionable alerts, Azure Workbooks and cost budgets.

**Acceptance goal:** Demonstrate error investigations, appropriate alerts and controlled dev-environment spend.

Separate internet edge, workload identity, CI credentials, control plane and data plane. Private services require a reachable private runner or network path. Verify DNS, routing, firewall, quotas and regional availability. This is an offline scaffold, NOT deployed production architecture.
