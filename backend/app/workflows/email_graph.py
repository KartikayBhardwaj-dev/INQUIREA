from langgraph.graph import (
    END,
    StateGraph,
)

from backend.app.workflows.workflow_state import (
    WorkflowState,
)

from backend.app.workflows.email_nodes import (
    supervisor_node,
    analysis_node,
    reply_node,
    memory_node,
)


def route_after_supervisor(state):
    return state.get(
        "next_agent",
        "analysis",
    )


def build_graph():

    graph = StateGraph(
        WorkflowState
    )

    graph.add_node(
        "supervisor",
        supervisor_node,
    )

    graph.add_node(
        "analysis",
        analysis_node,
    )

    graph.add_node(
        "reply",
        reply_node,
    )

    graph.add_node(
        "memory",
        memory_node,
    )

    graph.set_entry_point(
        "supervisor"
    )

    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "analysis": "analysis",
            "reply": "reply",
        },
    )

    graph.add_edge(
        "analysis",
        "memory",
    )

    graph.add_edge(
        "reply",
        "memory",
    )

    graph.add_edge(
        "memory",
        END,
    )

    return graph