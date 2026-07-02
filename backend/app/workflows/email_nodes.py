import asyncio
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from groq import (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
)

from backend.app.agents.registry import AgentRegistry


@retry(
    retry=retry_if_exception_type(
        (
            APIConnectionError,
            APITimeoutError,
            RateLimitError,
        )
    ),
    stop=stop_after_attempt(5),  # Increased retry attempts to break through harsh rate limits
    wait=wait_exponential(
        multiplier=2,            # Increased wait multiplier to allow the 6000 TPM window to clear
        min=4,
        max=20,
    ),
    reraise=True,
)
async def run_agent(agent_name, state, config=None):
    agent = AgentRegistry.get(agent_name)

    # Extract the live DB session securely from the runtime configuration context
    db_session = None
    if config and "configurable" in config:
        db_session = config["configurable"].get("db")

    # Clone the graph dictionary state strictly for the isolated lifecycle of this execution
    runtime_state = dict(state)
    runtime_state["db"] = db_session

    result = await agent.run(runtime_state)

    if not result["success"]:
        raise RuntimeError(
            f"{agent_name} failed: {result['error']}"
        )

    # EXTRACT AND CLEAN REGION:
    agent_output = result["result"]
    
    # Forcefully pop 'db' out of the returned dictionary if the agent returned the whole state mutated
    if isinstance(agent_output, dict):
        agent_output.pop("db", None)

    return agent_output


async def supervisor_node(state, config=None):
    return await run_agent(
        "supervisor_agent",
        state,
        config=config,
    )


async def analysis_node(state, config=None):
    return await run_agent(
        "analysis_agent",
        state,
        config=config,
    )


async def reply_node(state, config=None):
    return await run_agent(
        "reply_agent",
        state,
        config=config,
    )


async def memory_node(state, config=None):
    return await run_agent(
        "memory_agent",
        state,
        config=config,
    )