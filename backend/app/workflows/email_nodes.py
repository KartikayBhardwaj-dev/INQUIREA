from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from backend.app.agents.registry import (
    AgentRegistry,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(
        multiplier=1,
        min=2,
        max=10,
    ),
)
async def run_agent(
    agent_name,
    state,
):

    agent = AgentRegistry.get(
        agent_name
    )

    result = await agent.run(
        state
    )

    if not result["success"]:
        raise Exception(
            result["error"]
        )

    return result["result"]


async def supervisor_node(
    state,
):

    return await run_agent(
        "supervisor_agent",
        state,
    )


async def classification_node(
    state,
):

    return await run_agent(
        "classification_agent",
        state,
    )


async def extraction_node(
    state,
):

    return await run_agent(
        "extraction_agent",
        state,
    )


async def summary_node(
    state,
):

    return await run_agent(
        "summary_agent",
        state,
    )


async def reply_node(
    state,
):

    return await run_agent(
        "reply_agent",
        state,
    )


async def memory_node(
    state,
):

    return await run_agent(
        "memory_agent",
        state,
    )