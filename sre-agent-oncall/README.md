# SRE Agent Oncall

An autonomous SRE oncall agent built with LangGraph and Claude. Ingests alerts from PagerDuty and Prometheus, diagnoses incidents in parallel, and either auto-remediates or escalates to the infra owner.

## Architecture

```
alert intake (PagerDuty / Prometheus webhook)
    ↓
diagnose  ← parallel: kubectl logs + describe + RAG runbook lookup + PD enrichment
    ↓
synthesize  ← Claude picks summary + remediation action
    ↓
remediate  ← execute action or escalate to infra owner
    ↓
respond  ← tiered Slack notification (P0–P4)
```

## Project Structure

```
sre-agent-oncall/
├── pyproject.toml
├── Dockerfile
├── .env.example
├── checklist.md
├── runbooks/
│   ├── crashloop.md
│   ├── node-unhealthy.md
│   └── resource-starvation.md
├── systemd/
│   └── sre-agent.service
└── src/sre_agent/
    ├── config.py          — Settings via pydantic-settings
    ├── state.py           — IncidentState, Alert, RemediationAction types
    ├── main.py            — FastAPI webhooks (/webhook/pagerduty, /webhook/prometheus)
    ├── graph.py           — LangGraph workflow wiring
    ├── tools/
    │   ├── kubectl.py     — logs, describe (read) + restart, drain (write)
    │   ├── pagerduty.py   — alert enrichment + infra escalation
    │   ├── slack.py       — tiered P0–P4 notifications
    │   └── prometheus.py  — PromQL metric queries
    ├── rag/
    │   ├── ingest.py      — markdown → chunk → embed → Chroma
    │   └── retriever.py   — hybrid BM25 + semantic search
    └── nodes/
        ├── diagnose.py    — parallel fan-out (asyncio.gather)
        ├── synthesize.py  — Claude picks summary + action
        ├── remediate.py   — executes action or escalates
        └── respond.py     — Slack tiered response
```

## Remediation Policy

| Scenario | Agent Action |
|---|---|
| Pod CrashLoopBackOff | Auto-restart deployment |
| Node NotReady | Auto-drain (cordon + evict) |
| Resource starvation | Escalate to infra owner — no auto-scale |
| Traffic spike / HPA | Escalate to infra owner — no HPA override |
| Informational alert | Slack summary, no action |

Scaling and HPA adjustments are intentionally out of scope for the agent. These are escalated to the infra owner via PagerDuty and posted to `#infra-escalations`.

## Slack Notification Tiers

| Severity | Behaviour |
|---|---|
| P3 / P4 | Slack summary + runbook link |
| P2 | Slack + auto-restart safe pods |
| P1 | Slack + page oncall + attempt remediation |
| P0 | All above + escalation thread |

## Getting Started

### 1. Configure environment

```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, PD_TOKEN, SLACK_TOKEN, etc.
```

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Ingest runbooks

```bash
python -m sre_agent.rag.ingest
```

This is a one-time step (also runs automatically during Docker build).

### 4. Run the agent

```bash
python -m sre_agent.main
# Listening on http://0.0.0.0:8080
```

### 5. Point webhooks at the agent

| Source | Endpoint |
|---|---|
| PagerDuty | `POST /webhook/pagerduty` |
| Prometheus / Alertmanager | `POST /webhook/prometheus` |
| Health check | `GET /healthz` |

## Docker

```bash
docker build -t sre-agent .
docker run --env-file .env -p 8080:8080 sre-agent
```

## Systemd (Droplet deployment)

```bash
cp systemd/sre-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now sre-agent
journalctl -u sre-agent -f
```

## Adding Runbooks

Drop any `.md` file into `runbooks/` and re-run the ingest script. The agent uses hybrid BM25 + semantic search to match alerts against runbooks at diagnosis time.

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `KUBECONFIG` | Path to kubeconfig (leave empty for in-cluster) |
| `PD_TOKEN` | PagerDuty API token |
| `PD_SERVICE_ID` | PagerDuty service ID for escalation incidents |
| `PD_INFRA_ESCALATION_POLICY_ID` | PagerDuty escalation policy for infra owner |
| `SLACK_TOKEN` | Slack bot token (`xoxb-...`) |
| `SLACK_ONCALL_CHANNEL` | Channel for oncall alerts (default: `#oncall`) |
| `SLACK_INFRA_CHANNEL` | Channel for infra escalations (default: `#infra-escalations`) |
| `PROMETHEUS_URL` | Prometheus base URL |
| `CHROMA_PERSIST_DIR` | Directory for Chroma vector store |
| `RUNBOOKS_DIR` | Directory containing runbook markdown files |
| `MODEL` | Claude model ID (default: `claude-sonnet-4-6`) |
