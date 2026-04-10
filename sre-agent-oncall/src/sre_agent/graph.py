"""
LangGraph workflow:

  intake (alert validated)
      ↓
  diagnose  ← parallel: kubectl logs + describe + RAG + PD enrichment
      ↓
  synthesize  ← Claude picks summary + action
      ↓
  remediate  ← execute action or escalate
      ↓
  respond  ← tiered Slack notification
"""

from langgraph.graph import StateGraph, END

from sre_agent.state import IncidentState
from sre_agent.nodes.diagnose import diagnose
from sre_agent.nodes.synthesize import synthesize
from sre_agent.nodes.remediate import remediate
from sre_agent.nodes.respond import respond


def build_graph() -> StateGraph:
    builder = StateGraph(IncidentState)

    builder.add_node("diagnose", diagnose)
    builder.add_node("synthesize", synthesize)
    builder.add_node("remediate", remediate)
    builder.add_node("respond", respond)

    builder.set_entry_point("diagnose")
    builder.add_edge("diagnose", "synthesize")
    builder.add_edge("synthesize", "remediate")
    builder.add_edge("remediate", "respond")
    builder.add_edge("respond", END)

    return builder.compile()
