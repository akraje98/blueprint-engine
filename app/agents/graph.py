from langgraph.graph import StateGraph, END
from app.schemas.agent_state import BlueprintAgentState
from app.agents.nodes import BlueprintNodes

def route_after_audit(state: BlueprintAgentState) -> str:
    """
    Conditional Edge Router:
    If a timeline clash exists, stop and surface the conflict warning to the user.
    If clear, proceed to persist the data into Neo4j and Valkey.
    """
    audit_report = state.get("audit_report", {})
    if audit_report.get("has_conflict", False):
        print("🛑 [Graph Router] Conflict detected! Halting save and surfacing warning.")
        return END
    
    print("✅ [Graph Router] Audit passed! Routing to persistence layer.")
    return "persistence"

def build_blueprint_graph():
    """Compiles the stateful multi-agent workflow graph."""
    workflow = StateGraph(BlueprintAgentState)

    # 1. Register all three worker nodes
    workflow.add_node("parser", BlueprintNodes.parsing_router_node)
    workflow.add_node("auditor", BlueprintNodes.conflict_auditor_node)
    workflow.add_node("persistence", BlueprintNodes.persistence_node)

    # 2. Define flow: parser -> auditor -> conditional check -> persistence -> END
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "auditor")
    workflow.add_conditional_edges(
        "auditor",
        route_after_audit,
        {
            "persistence": "persistence",
            END: END
        }
    )
    workflow.add_edge("persistence", END)

    return workflow.compile()

blueprint_graph = build_blueprint_graph()
