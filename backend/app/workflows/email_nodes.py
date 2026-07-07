from backend.app.agents.registry import AgentRegistry


async def run_agent(
    agent_name: str,
    state: dict,
    config=None,
):
    """
    Execute an agent and return its output.

    The database session (if supplied through LangGraph config)
    is injected into the runtime state but removed before the
    state continues through the workflow.
    """

    agent = AgentRegistry.get(agent_name)

    db_session = None

    if config:
        db_session = (
            config.get("configurable", {})
            .get("db")
        )

    runtime_state = dict(state)

    if db_session is not None:
        runtime_state["db"] = db_session

    result = await agent.run(runtime_state)

    if not result["success"]:
        raise RuntimeError(
            f"{agent_name}: {result['error']}"
        )

    output = result["result"]

    if isinstance(output, dict):
        output.pop("db", None)

    return output


async def analysis_node(
    state,
    config=None,
):
    """
    Single workflow step.

    AnalysisAgent performs:
    - Category
    - Priority
    - Summary
    - Reply Required
    - Extracted Entities
    """

    return await run_agent(
        "analysis_agent",
        state,
        config,
    )