from abc import ABC
from abc import abstractmethod

from backend.app.agents.state import (
    AgentState,
)

from backend.app.database.session import (
    SessionLocal,
)

from backend.app.models.agent_run import (
    AgentRun,
)


class BaseAgent(ABC):

    name = "base"

    async def run(
        self,
        state: AgentState,
    ):

        db = SessionLocal()

        try:

            result = await self.execute(
                state
            )

            db.add(
                AgentRun(
                    agent_name=self.name,
                    email_id=state.get("email_id"),
                    success=True,
                    result=result.model_dump()
                    if hasattr(
                        result,
                        "model_dump",
                    )
                    else result,
                )
            )

            db.commit()

            return {
                "success": True,
                "agent": self.name,
                "result": result,
                "error": None,
            }

        except Exception as e:

            db.add(
                AgentRun(
                    agent_name=self.name,
                    email_id=state.get("email_id"),
                    success=False,
                    result={
                        "error": str(e)
                    },
                )
            )

            db.commit()

            state.setdefault(
    "errors",
    []
).append(
    str(e)
)

            return {
                "success": False,
                "agent": self.name,
                "result": None,
                "error": str(e),
            }

        finally:
            db.close()

    @abstractmethod
    async def execute(
        self,
        state,
    ):
        pass