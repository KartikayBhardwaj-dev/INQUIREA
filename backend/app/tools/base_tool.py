from abc import ABC
from abc import abstractmethod


class BaseTool(ABC):

    name = "tool"

    @abstractmethod
    async def execute(
        self,
        **kwargs,
    ):
        pass