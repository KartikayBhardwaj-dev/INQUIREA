from fastapi import APIRouter
from fastapi import HTTPException

from backend.app.agents.registry import (
    AgentRegistry,
)

from backend.app.agents.state import (
    AgentState,
)

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.get("/")
async def list_agents():

    return {
        "agents": list(
            AgentRegistry._agents.keys()
        )
    }





@router.get("/classification")
async def run_classification_agent():

    agent = AgentRegistry.get(
        "classification_agent"
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    state = AgentState()

    state.subject = (
        "Software Engineering Internship"
    )

    state.body = (
        "We are hiring interns for our AI team."
    )

    state.sender = (
        "careers@company.com"
    )

    result = await agent.run(
        state
    )

    return result


@router.post("/{agent_name}")
async def run_agent(
    agent_name: str,
):

    agent = AgentRegistry.get(
        agent_name
    )

    if not agent:

        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    result = await agent.run(
        AgentState()
    )

    return result