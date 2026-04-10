"""PagerDuty: alert enrichment + infra owner escalation."""

import logging
import httpx
from sre_agent.config import settings

log = logging.getLogger(__name__)
BASE = "https://api.pagerduty.com"
HEADERS = {
    "Authorization": f"Token token={settings.pd_token}",
    "Accept": "application/vnd.pagerduty+json;version=2",
    "Content-Type": "application/json",
}


def get_alert_context(incident_id: str) -> str:
    """Fetch incident notes and metadata from PagerDuty."""
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(f"{BASE}/incidents/{incident_id}", headers=HEADERS)
            r.raise_for_status()
            inc = r.json().get("incident", {})
            return (
                f"Title: {inc.get('title')}\n"
                f"Status: {inc.get('status')}\n"
                f"Urgency: {inc.get('urgency')}\n"
                f"Created: {inc.get('created_at')}\n"
                f"Body: {inc.get('body', {}).get('details', '')}"
            )
    except Exception as exc:
        log.warning("PD context fetch failed: %s", exc)
        return f"ERROR: {exc}"


def escalate_to_infra_owner(alert_title: str, reason: str, alert_id: str) -> str:
    """
    Create a new PagerDuty incident targeted at the infra escalation policy.
    Used for resource starvation and traffic spike scenarios.
    """
    payload = {
        "incident": {
            "type": "incident",
            "title": f"[ESCALATED] {alert_title}",
            "service": {"id": settings.pd_service_id, "type": "service_reference"},
            "escalation_policy": {
                "id": settings.pd_infra_escalation_policy_id,
                "type": "escalation_policy_reference",
            },
            "body": {
                "type": "incident_body",
                "details": (
                    f"SRE Agent escalated this incident to infra owner.\n\n"
                    f"Original Alert ID: {alert_id}\n"
                    f"Reason: {reason}\n\n"
                    "This requires manual intervention: scaling or HPA adjustment."
                ),
            },
        }
    }
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(f"{BASE}/incidents", headers=HEADERS, json=payload)
            r.raise_for_status()
            inc_id = r.json()["incident"]["id"]
            return f"Escalated to infra owner — PD incident {inc_id}"
    except Exception as exc:
        log.error("PD escalation failed: %s", exc)
        return f"ERROR: {exc}"
