from backend.app.agents.base_agent import (
    BaseAgent,
)


class ClassificationAgent(
    BaseAgent
):

    name = "classification_agent"

    async def execute(
        self,
        state,
    ):

        return {
            "category": "job",
            "priority": "high",
        }