"""
Remediate node.
Executes the action chosen by synthesize:
  - restart_pod    → kubectl rollout restart
  - drain_node     → kubectl cordon + evict
  - escalate_infra → PagerDuty escalation to infra owner (no scaling done here)
  - no_action      → skip
"""

import logging
from sre_agent.state import IncidentState, RemediationAction

log = logging.getLogger(__name__)


async def remediate(state: IncidentState) -> dict:
    alert = state.alert
    action = state.action

    from sre_agent.tools import kubectl, pagerduty

    output = ""
    escalated = False

    if action == RemediationAction.RESTART_POD:
        if not alert.pod:
            output = "No pod specified — skipping restart"
        else:
            output = kubectl.restart_deployment(alert.namespace, alert.pod)

    elif action == RemediationAction.DRAIN_NODE:
        if not alert.node:
            output = "No node specified — skipping drain"
        else:
            output = kubectl.drain_node(alert.node)

    elif action == RemediationAction.ESCALATE_INFRA:
        reason = (
            "Resource starvation or traffic spike detected. "
            "Manual scaling or HPA adjustment required — agent will not act."
        )
        pd_result = pagerduty.escalate_to_infra_owner(alert.title, reason, alert.id)
        output = pd_result
        escalated = True

    elif action == RemediationAction.NO_ACTION:
        output = "No remediation needed."

    log.info("Remediation result for %s: %s", alert.id, output)
    return {"action_output": output, "escalated": escalated}
