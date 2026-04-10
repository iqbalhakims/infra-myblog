"""Read-only kubectl tools + safe write actions (restart, drain only)."""

import logging
from kubernetes import client, config as kube_config
from sre_agent.config import settings

log = logging.getLogger(__name__)


def _load_kube() -> None:
    if settings.kubeconfig:
        kube_config.load_kube_config(config_file=settings.kubeconfig)
    else:
        kube_config.load_incluster_config()


# ── Read tools ────────────────────────────────────────────────────────────────

def get_pod_logs(namespace: str, pod: str, tail: int = 100) -> str:
    _load_kube()
    v1 = client.CoreV1Api()
    try:
        return v1.read_namespaced_pod_log(
            name=pod, namespace=namespace, tail_lines=tail, timestamps=True
        )
    except Exception as exc:
        log.warning("get_pod_logs failed: %s", exc)
        return f"ERROR: {exc}"


def describe_pod(namespace: str, pod: str) -> str:
    _load_kube()
    v1 = client.CoreV1Api()
    try:
        pod_obj = v1.read_namespaced_pod(name=pod, namespace=namespace)
        containers = pod_obj.status.container_statuses or []
        lines = [f"Phase: {pod_obj.status.phase}"]
        for cs in containers:
            state = cs.state
            if state.waiting:
                lines.append(f"Container {cs.name}: Waiting — {state.waiting.reason}")
            elif state.terminated:
                lines.append(
                    f"Container {cs.name}: Terminated — exit={state.terminated.exit_code}"
                )
            else:
                lines.append(f"Container {cs.name}: Running")
            lines.append(f"  RestartCount: {cs.restart_count}")
        return "\n".join(lines)
    except Exception as exc:
        log.warning("describe_pod failed: %s", exc)
        return f"ERROR: {exc}"


def get_pod_status(namespace: str, pod: str) -> str:
    _load_kube()
    v1 = client.CoreV1Api()
    try:
        pod_obj = v1.read_namespaced_pod(name=pod, namespace=namespace)
        return pod_obj.status.phase or "Unknown"
    except Exception as exc:
        return f"ERROR: {exc}"


# ── Write tools (safe remediation only) ──────────────────────────────────────

def restart_deployment(namespace: str, pod: str) -> str:
    """Restart the deployment owning the given pod via rollout restart."""
    _load_kube()
    v1 = client.CoreV1Api()
    apps = client.AppsV1Api()
    try:
        pod_obj = v1.read_namespaced_pod(name=pod, namespace=namespace)
        owner = next(
            (r for r in (pod_obj.metadata.owner_references or []) if r.kind == "ReplicaSet"),
            None,
        )
        if not owner:
            return "ERROR: could not find owning ReplicaSet"

        rs = apps.read_namespaced_replica_set(name=owner.name, namespace=namespace)
        deploy_owner = next(
            (r for r in (rs.metadata.owner_references or []) if r.kind == "Deployment"),
            None,
        )
        if not deploy_owner:
            return "ERROR: could not find owning Deployment"

        import datetime, json
        patch = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow().isoformat()
                        }
                    }
                }
            }
        }
        apps.patch_namespaced_deployment(
            name=deploy_owner.name, namespace=namespace, body=patch
        )
        return f"Restarted deployment/{deploy_owner.name} in {namespace}"
    except Exception as exc:
        log.error("restart_deployment failed: %s", exc)
        return f"ERROR: {exc}"


def drain_node(node_name: str) -> str:
    """Cordon + evict all pods from an unhealthy node."""
    _load_kube()
    v1 = client.CoreV1Api()
    try:
        # Cordon
        v1.patch_node(node_name, {"spec": {"unschedulable": True}})

        # Evict all non-daemonset pods
        pods = v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}")
        evicted = []
        for pod in pods.items:
            owners = pod.metadata.owner_references or []
            if any(o.kind == "DaemonSet" for o in owners):
                continue
            eviction = client.V1Eviction(
                metadata=client.V1ObjectMeta(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                )
            )
            try:
                v1.create_namespaced_pod_eviction(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    body=eviction,
                )
                evicted.append(pod.metadata.name)
            except Exception as e:
                log.warning("Could not evict %s: %s", pod.metadata.name, e)

        return f"Cordoned {node_name} and evicted {len(evicted)} pods: {evicted}"
    except Exception as exc:
        log.error("drain_node failed: %s", exc)
        return f"ERROR: {exc}"
