from abc import ABC
from abc import abstractmethod


class BaseAgent(ABC):

    name = "base"

    async def run(
        self,
        state,
    ):

        try:

            result = await self.execute(
                state
            )

            return {
                "success": True,
                "agent": self.name,
                "result": result,
                "error": None,
            }

        except Exception as e:

            return {
                "success": False,
                "agent": self.name,
                "result": None,
                "error": str(e),
            }

    @abstractmethod
    async def execute(
        self,
        state,
    ):
        pass