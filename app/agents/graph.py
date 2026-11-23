from langgraph.graph import StateGraph, END
from app.schemas.agent_state import BlueprintAgentState
from app.agents.nodes import BlueprintNodes

def should_continue_or_loop(state: BlueprintAgentState) -> str:
    """
    Conditional Edge Router:
    Checks the Conflict Auditor's report. If a timeline clash exists, 
    route back to the parser to self-correct. Otherwise, finish execution.
    """
    audit_report = state.get("audit_report", {})
    if audit_report.get("has_conflict", False):
        print("🔄 [Graph Router] Conflict detected! Looping back to LLM Router for self-correction...")
        return "parser"
    
    print("🏁 [Graph Router] No conflicts detected. Finalizing workflow.")
    return END

def build_blueprint_graph():
    """Compiles the stateful multi-agent workflow graph."""
    workflow = StateGraph(BlueprintAgentState)

    # 1. Register the worker nodes
    workflow.add_node("parser", BlueprintNodes.parsing_router_node)
    workflow.add_node("auditor", BlueprintNodes.conflict_auditor_node)

    # 2. Define the entry point
    workflow.set_entry_point("parser")

    # 3. Connect parser -> auditor
    workflow.add_edge("parser", "auditor")

    # 4. Add the conditional self-correction loop after auditing
    workflow.add_conditional_edges(
        "auditor",
        should_continue_or_loop,
        {
            "parser": "parser",
            END: END
        }
    )

    # Compile into an executable LangGraph runnable
    return workflow.compile()

# Single global compiled graph instance
blueprint_graph = build_blueprint_graph()
