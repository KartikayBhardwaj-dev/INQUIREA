from backend.app.agents.base_agent import (
    BaseAgent,
)

from backend.app.memory.vector_store import (
    VectorMemory,
)


class MemoryAgent(BaseAgent):

    name = "memory_agent"

    async def execute(
        self,
        state,
    ):

        email_id = state["email_id"]

        memory_text = f"""
Subject:
{state['subject']}

Category:
{state.get('category')}

Priority:
{state.get('priority')}

Summary:
{state.get('summary')}

Thread Summary:
{state.get('thread_summary')}
"""

        VectorMemory.store(
            email_id=email_id,
            content=memory_text,
            metadata={
                "email_id": email_id,
                "category":
                state.get("category"),
                "priority":
                state.get("priority"),
            },
        )

        state["memory"] = {
            "stored": True,
            "email_id": email_id,
        }

        return state

    async def retrieve(
        self,
        query: str,
    ):

        return VectorMemory.search(
            query=query,
            limit=5,
        )