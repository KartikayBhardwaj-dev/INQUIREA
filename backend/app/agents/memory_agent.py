from backend.app.agents.base_agent import BaseAgent


class MemoryAgent(BaseAgent):

    name = "memory_agent"

    async def execute(
        self,
        state,
    ):

        state["memory"] = {
            "indexed": False,
            "email_id": state["email_id"],
        }

        return state