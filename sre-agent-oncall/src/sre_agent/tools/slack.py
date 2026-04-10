"""Slack: tiered incident notifications."""

import logging
import httpx
from sre_agent.config import settings
from sre_agent.state import Severity

log = logging.getLogger(__name__)
BASE = "https://slack.com/api"
HEADERS = {"Authorization": f"Bearer {settings.slack_token}"}

SEVERITY_EMOJI = {
    Severity.P0: ":rotating_light:",
    Severity.P1: ":red_circle:",
    Severity.P2: ":large_orange_circle:",
    Severity.P3: ":large_yellow_circle:",
    Severity.P4: ":white_circle:",
}


def _post(channel: str, text: str, thread_ts: str = "") -> str:
    payload: dict = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(f"{BASE}/chat.postMessage", headers=HEADERS, json=payload)
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                log.warning("Slack error: %s", data.get("error"))
            return data.get("ts", "")
    except Exception as exc:
        log.error("Slack post failed: %s", exc)
        return ""


def notify(
    severity: Severity,
    alert_title: str,
    summary: str,
    action_taken: str,
    runbook_snippet: str = "",
    thread_ts: str = "",
) -> str:
    """
    Post tiered incident message to #oncall.
    Returns thread_ts for follow-up replies.
    """
    emoji = SEVERITY_EMOJI.get(severity, ":white_circle:")
    blocks = [
        f"{emoji} *[{severity}] {alert_title}*",
        f"*Summary:* {summary}",
        f"*Action:* {action_taken}",
    ]
    if runbook_snippet:
        blocks.append(f"*Runbook:* {runbook_snippet[:300]}")

    text = "\n".join(blocks)
    return _post(settings.slack_oncall_channel, text, thread_ts)


def notify_infra_escalation(alert_title: str, reason: str, pd_incident_id: str) -> str:
    """Post escalation notice to #infra-escalations."""
    text = (
        f":escalator: *Infra Escalation Required*\n"
        f"*Alert:* {alert_title}\n"
        f"*Reason:* {reason}\n"
        f"*PD Incident:* {pd_incident_id}\n"
        "Agent cannot auto-remediate — manual scaling/HPA adjustment needed."
    )
    return _post(settings.slack_infra_channel, text)
