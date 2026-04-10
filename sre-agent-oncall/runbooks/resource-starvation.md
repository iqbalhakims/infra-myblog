# Runbook: Resource Starvation / Traffic Spike

## Symptoms
- High CPU throttling across multiple pods
- Request latency increasing
- HPA at max replicas
- Pending pods due to insufficient cluster capacity

## Common Causes
1. Unexpected traffic surge
2. Misconfigured resource requests/limits
3. Cluster autoscaler lag
4. Noisy neighbour consuming shared resources

## Diagnosis Steps
1. Check HPA status: `kubectl get hpa -n <namespace>`
2. Check pending pods: `kubectl get pods -n <namespace> | grep Pending`
3. Check node capacity: `kubectl describe nodes | grep -A5 Allocated`
4. Query Prometheus for request rate and latency

## Remediation
> **This runbook requires infra owner action.**
> The SRE agent will NOT auto-scale or adjust HPA.

1. Infra owner to evaluate current HPA max replicas
2. Consider increasing node pool size via cluster autoscaler config
3. Review and right-size resource requests if consistently throttled
4. For traffic spikes: evaluate CDN caching or rate limiting at ingress

## Agent Action
- `escalate_infra` — page infra owner with full context
- Agent posts to #infra-escalations with Prometheus metrics
