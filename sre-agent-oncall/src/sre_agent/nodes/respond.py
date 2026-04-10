"""
Respond node.
Posts tiered Slack notification. For escalations, also posts to #infra-escalations.
"""

import logging
from sre_agent.state import IncidentState, Severity, RemediationAction
from sre_agent.tools import slack

log = logging.getLogger(__name__)


async def respond(state: IncidentState) -> dict:
    alert = state.alert
    diag = state.diagnosis

    action_label = {
        RemediationAction.RESTART_POD: "Restarted deployment",
        RemediationAction.DRAIN_NODE: "Drained node",
        RemediationAction.ESCALATE_INFRA: "Escalated to infra owner — no auto-remediation",
        RemediationAction.NO_ACTION: "No action taken",
    }.get(state.action, "Unknown")

    action_text = f"{action_label}: {state.action_output}"

    thread_ts = slack.notify(
        severity=alert.severity,
        alert_title=alert.title,
        summary=diag.summary,
        action_taken=action_text,
        runbook_snippet=diag.runbook,
        thread_ts=state.slack_thread_ts,
    )

    if state.escalated:
        slack.notify_infra_escalation(
            alert_title=alert.title,
            reason=diag.summary,
            pd_incident_id=state.action_output,
        )

    log.info("Slack notification sent for alert %s (thread=%s)", alert.id, thread_ts)
    return {"slack_thread_ts": thread_ts}
