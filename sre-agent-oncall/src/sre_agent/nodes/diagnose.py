"""
Parallel diagnosis node.
Fans out to: kubectl logs, kubectl describe, RAG lookup, PD enrichment.
All run concurrently via asyncio.gather.
"""

import asyncio
import logging
from functools import partial

from sre_agent.state import IncidentState, DiagnosisResult

log = logging.getLogger(__name__)


def _run_sync(fn, *args):
    """Run a blocking function in the default executor."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, partial(fn, *args))


async def diagnose(state: IncidentState) -> dict:
    alert = state.alert
    if not alert:
        return {}

    from sre_agent.tools import kubectl, pagerduty
    from sre_agent.rag.retriever import retrieve

    query = f"{alert.title} {' '.join(alert.labels.values())}"

    tasks = [
        _run_sync(kubectl.get_pod_logs, alert.namespace, alert.pod or "") if alert.pod else asyncio.sleep(0, result="no pod"),
        _run_sync(kubectl.describe_pod, alert.namespace, alert.pod or "") if alert.pod else asyncio.sleep(0, result="no pod"),
        _run_sync(retrieve, query),
        _run_sync(pagerduty.get_alert_context, alert.id) if alert.source == "pagerduty" else asyncio.sleep(0, result=""),
    ]

    logs, describe, runbook, pd_ctx = await asyncio.gather(*tasks)

    diagnosis = DiagnosisResult(
        kubectl_logs=str(logs),
        kubectl_describe=str(describe),
        runbook=str(runbook),
        pd_context=str(pd_ctx),
    )
    log.info("Diagnosis complete for alert %s", alert.id)
    return {"diagnosis": diagnosis}
