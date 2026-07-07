from langgraph.graph import END, StateGraph

from backend.app.workflows.workflow_state import WorkflowState
from backend.app.workflows.email_nodes import (
    analysis_node,
    persistence_node,
)


def build_graph():
    """
    Simplified ingestion workflow.

    Email
        ↓
    Analysis
        ↓
    Persistence
        ↓
    Queue Embedding (inside persistence)
        ↓
    END
    """

    graph = StateGraph(WorkflowState)

    graph.add_node(
        "analysis",
        analysis_node,
    )

    graph.add_node(
        "persistence",
        persistence_node,
    )

    graph.set_entry_point("analysis")

    graph.add_edge(
        "analysis",
        "persistence",
    )

    graph.add_edge(
        "persistence",
        END,
    )

    return graph.compile()