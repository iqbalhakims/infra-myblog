# Runbook: CrashLoopBackOff

## Symptoms
- Pod status shows `CrashLoopBackOff`
- High restart count on container
- Exit code non-zero (OOMKilled, error, segfault)

## Common Causes
1. Application error at startup (bad config, missing env var)
2. OOMKilled — container exceeds memory limit
3. Liveness probe misconfigured — kills healthy container
4. Dependency not ready (DB, external service)

## Diagnosis Steps
1. `kubectl logs <pod> --previous` — check last crash output
2. `kubectl describe pod <pod>` — check Events and last state
3. Look for `OOMKilled` in `lastState.terminated.reason`

## Remediation
- **Config/env error**: Fix the deployment env vars and rollout restart
- **OOMKilled**: Increase memory limits — escalate to infra if limits already high
- **Probe failure**: Adjust `initialDelaySeconds` on liveness probe
- **Dependency**: Wait for dependency or fix connection string

## Agent Action
- `restart_pod` if exit code is non-OOM application error
- `escalate_infra` if OOMKilled and resource limits need changing
