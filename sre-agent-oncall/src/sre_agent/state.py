from __future__ import annotations

from enum import Enum
from typing import Annotated

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class RemediationAction(str, Enum):
    RESTART_POD = "restart_pod"
    DRAIN_NODE = "drain_node"
    ESCALATE_INFRA = "escalate_infra"
    NO_ACTION = "no_action"


class Alert(BaseModel):
    id: str
    title: str
    severity: Severity
    namespace: str = "default"
    pod: str | None = None
    node: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    source: str = "pagerduty"  # pagerduty | prometheus


class DiagnosisResult(BaseModel):
    kubectl_logs: str = ""
    kubectl_describe: str = ""
    runbook: str = ""
    pd_context: str = ""
    summary: str = ""


class IncidentState(BaseModel):
    alert: Alert | None = None
    diagnosis: DiagnosisResult = Field(default_factory=DiagnosisResult)
    action: RemediationAction = RemediationAction.NO_ACTION
    action_output: str = ""
    escalated: bool = False
    slack_thread_ts: str = ""
    messages: Annotated[list, add_messages] = Field(default_factory=list)
