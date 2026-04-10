"""Entrypoint: FastAPI webhook server that feeds alerts into the LangGraph agent."""

import logging

import uvicorn
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from sre_agent.graph import build_graph
from sre_agent.state import Alert, Severity

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="SRE Agent Oncall")
graph = build_graph()


class PagerDutyWebhook(BaseModel):
    event: dict


class PrometheusWebhook(BaseModel):
    alerts: list[dict]


async def run_agent(alert: Alert) -> None:
    log.info("Running agent for alert %s (%s)", alert.id, alert.title)
    from sre_agent.state import IncidentState
    result = await graph.ainvoke(IncidentState(alert=alert))
    log.info("Agent finished for alert %s — action=%s", alert.id, result["action"])


@app.post("/webhook/pagerduty")
async def pagerduty_webhook(payload: PagerDutyWebhook, bg: BackgroundTasks):
    event = payload.event
    alert = Alert(
        id=event.get("id", "unknown"),
        title=event.get("title", "Unknown alert"),
        severity=Severity(event.get("priority", {}).get("name", "P3")),
        namespace=event.get("details", {}).get("namespace", "default"),
        pod=event.get("details", {}).get("pod"),
        node=event.get("details", {}).get("node"),
        labels=event.get("details", {}).get("labels", {}),
        source="pagerduty",
    )
    bg.add_task(run_agent, alert)
    return {"status": "accepted", "alert_id": alert.id}


@app.post("/webhook/prometheus")
async def prometheus_webhook(payload: PrometheusWebhook, bg: BackgroundTasks):
    for raw in payload.alerts:
        labels = raw.get("labels", {})
        alert = Alert(
            id=raw.get("fingerprint", "unknown"),
            title=labels.get("alertname", "Unknown"),
            severity=Severity(labels.get("severity", "P3").upper()),
            namespace=labels.get("namespace", "default"),
            pod=labels.get("pod"),
            node=labels.get("node"),
            labels=labels,
            source="prometheus",
        )
        bg.add_task(run_agent, alert)
    return {"status": "accepted", "count": len(payload.alerts)}


@app.get("/healthz")
def health():
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run("sre_agent.main:app", host="0.0.0.0", port=8080, reload=False)
