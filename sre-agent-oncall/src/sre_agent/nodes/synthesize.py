"""
Synthesize node.
Sends all diagnosis data to Claude and gets back:
  - a human-readable summary
  - a recommended RemediationAction
"""

import logging
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from sre_agent.config import settings
from sre_agent.state import IncidentState, RemediationAction

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert SRE oncall agent.
Given an alert and its diagnosis data, you must:
1. Write a concise incident summary (2-3 sentences).
2. Choose exactly ONE remediation action from this list:
   - restart_pod       → pod is crashlooping or in error state
   - drain_node        → node is unhealthy / not ready
   - escalate_infra    → resource starvation or traffic spike (DO NOT scale/HPA yourself)
   - no_action         → alert is informational or already resolved

Respond in this exact format:
SUMMARY: <summary text>
ACTION: <action_key>
"""


async def synthesize(state: IncidentState) -> dict:
    alert = state.alert
    diag = state.diagnosis

    prompt = f"""Alert: {alert.title} (Severity: {alert.severity}, Pod: {alert.pod}, Node: {alert.node})

Kubectl Logs:
{diag.kubectl_logs[:2000]}

Kubectl Describe:
{diag.kubectl_describe[:1000]}

PagerDuty Context:
{diag.pd_context[:500]}

Runbook Match:
{diag.runbook[:1500]}
"""

    llm = ChatAnthropic(
        model=settings.model,
        api_key=settings.anthropic_api_key,
        temperature=0,
    )
    response = await llm.ainvoke(
        [HumanMessage(content=prompt)],
        config={"system": SYSTEM_PROMPT},
    )
    text = response.content

    summary = ""
    action = RemediationAction.NO_ACTION
    for line in text.splitlines():
        if line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
        elif line.startswith("ACTION:"):
            raw = line.replace("ACTION:", "").strip()
            try:
                action = RemediationAction(raw)
            except ValueError:
                log.warning("Unknown action '%s', defaulting to no_action", raw)

    log.info("Synthesized: action=%s for alert %s", action, alert.id)
    diag.summary = summary
    return {"diagnosis": diag, "action": action}
