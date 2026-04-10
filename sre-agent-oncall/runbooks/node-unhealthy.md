# Runbook: Node NotReady / Unhealthy

## Symptoms
- Node status is `NotReady`
- Pods on node stuck in `Terminating` or `Unknown`
- Kubelet not reporting

## Common Causes
1. Disk pressure — node disk full
2. Memory pressure — node OOM
3. Network partition — kubelet cannot reach API server
4. VM crash or hardware failure

## Diagnosis Steps
1. `kubectl describe node <node>` — check Conditions and Events
2. Look for `DiskPressure`, `MemoryPressure`, `NetworkUnavailable` conditions
3. Check cloud provider console for VM health

## Remediation
- **Disk pressure**: SSH in, clear logs/tmp — or drain and replace
- **Memory pressure**: Drain node, investigate large pods
- **Network/VM failure**: Drain node immediately, let scheduler reschedule pods

## Agent Action
- `drain_node` — cordon + evict all non-DaemonSet pods
- After drain, alert infra team to investigate/replace node
