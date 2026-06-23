from backend.app.agents.base_agent import (
    BaseAgent,
)

from backend.app.tools.registry import (
    ToolRegistry,
)


class TestAgent(BaseAgent):

    name = "test_agent"

    async def execute(
        self,
        state,
    ):

        tool = ToolRegistry.get(
            "date_tool"
        )

        result = await tool.execute()

        return result