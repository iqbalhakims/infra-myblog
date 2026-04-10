Update Todos

Create new GitHub repo: sre-agent

Init project structure (Python + pyproject.toml or requirements.txt)

Set up LangGraph with parallel node execution (Send() API for fan-out diagnosis)

Set up vector store for RAG with hybrid search (BM25 + embeddings, e.g. Chroma or pgvector)

Create runbooks/ directory and add initial markdown runbooks

Build RAG ingestion pipeline (load runbooks → chunk → embed → store)

Build agent tools (read): kubectl logs, kubectl describe, pod status

Build agent tools (read): Prometheus/Alertmanager webhook intake

Build agent tools (read): PagerDuty alert intake + enrichment

Build agent tools (write — safe remediation only):
  - kubectl rollout restart (crashlooping pods)
  - kubectl drain (unhealthy nodes)

Build escalation tool: for resource starvation or traffic spikes, page infra owner via PagerDuty/Slack instead of acting

Build agent tools: Slack notification sender (tiered by severity)
  - P3/P4 → Slack summary + runbook link
  - P2 → Slack + auto-restart safe pods
  - P1 → Slack + page oncall + attempt remediation
  - P0 → All above + escalation thread

Build incident state node: persist what was tried, what worked, feed outcomes back into RAG

Wire up LangGraph workflow:
  alert intake →
    (parallel) kubectl logs + kubectl describe + RAG lookup + PD enrichment →
  synthesize →
    remediate or escalate →
  respond via Slack

Add .env config: ANTHROPIC_API_KEY, KUBECONFIG, PD_TOKEN, SLACK_TOKEN, PROMETHEUS_URL

Write Dockerfile for Droplet deployment

Write deployment script or systemd service for Droplet

Test end-to-end: simulate alert → agent diagnoses → posts to Slack
Test escalation path: simulate resource starvation → agent pages infra owner
