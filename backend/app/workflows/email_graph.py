from contextlib import asynccontextmanager

from langgraph.graph import (
    END,
    StateGraph,
)

from langgraph.checkpoint.sqlite.aio import (
    AsyncSqliteSaver,
)

from backend.app.workflows.workflow_state import (
    WorkflowState,
)

from backend.app.workflows.email_nodes import (
    supervisor_node,
    classification_node,
    extraction_node,
    summary_node,
    reply_node,
    memory_node,
)


def route_after_supervisor(state):
    return state.get(
        "next_agent",
        "classification",
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
        "classification",
        classification_node,
    )

    graph.add_node(
        "extraction",
        extraction_node,
    )

    graph.add_node(
        "summary",
        summary_node,
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
            "classification": "classification",
            "reply": "reply",
        },
    )

    graph.add_edge(
        "classification",
        "extraction",
    )

    graph.add_edge(
        "extraction",
        "summary",
    )

    graph.add_edge(
        "summary",
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


@asynccontextmanager
async def get_email_graph():

    graph = build_graph()

    async with AsyncSqliteSaver.from_conn_string(
        "inquirea.db"
    ) as checkpointer:

        compiled = graph.compile(
            checkpointer=checkpointer
        )

        yield compiled