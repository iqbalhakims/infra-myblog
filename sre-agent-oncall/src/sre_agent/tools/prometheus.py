"""Prometheus: metric queries for enriching diagnosis."""

import logging
import httpx
from sre_agent.config import settings

log = logging.getLogger(__name__)


def query(promql: str) -> str:
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(
                f"{settings.prometheus_url}/api/v1/query",
                params={"query": promql},
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("data", {}).get("result", [])
            if not results:
                return "No data"
            lines = []
            for item in results[:10]:
                metric = item.get("metric", {})
                value = item.get("value", [None, "?"])[1]
                lines.append(f"{metric} => {value}")
            return "\n".join(lines)
    except Exception as exc:
        log.warning("Prometheus query failed: %s", exc)
        return f"ERROR: {exc}"


def pod_cpu_usage(namespace: str, pod: str) -> str:
    return query(f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}",pod="{pod}"}}[5m])')


def pod_memory_usage(namespace: str, pod: str) -> str:
    return query(f'container_memory_working_set_bytes{{namespace="{namespace}",pod="{pod}"}}')


def node_cpu_pressure(node: str) -> str:
    return query(f'rate(node_cpu_seconds_total{{mode!="idle",instance=~"{node}.*"}}[5m])')
